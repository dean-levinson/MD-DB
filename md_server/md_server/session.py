import os
import asyncio
import inspect
import logging
from collections import namedtuple
from unicodedata import name
from mdlib import md_pb2
from mdlib.md_pb2 import InitConnActions, Results, DBResult
from mdlib.exceptions import InvalidAction
from mdlib.md_pb2 import INIT_DONE
from mdlib.md_pb2 import DBMessage, MessageTypes, Results
from mdlib.socket_utils import LengthReader, LengthWriter
from mdlib.db_utils import get_db_md5, MDActions, EXCEPTIONS_TO_RESULT
from mdlib.exceptions import ClientNotAllowed, KeyDoesNotExists, KeyAlreadyExists

Handler = namedtuple("Handler", ["handler", "is_async"])
ExceptionTuple = namedtuple("ExceptionTuple", ["should_raise", "exception_type"])

def validate_args_kwargs(arguments):
    def decorator(func):
        def validator(*args, **kwargs):
            for arg in arguments:
                if arg not in kwargs.keys():
                    raise ValueError("{arg} must be in kwargs")

            return func(*args, **kwargs)
        return validator
    return decorator

class Session(object):
    def __init__(self, server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, directory: str):
        self.server = server
        self.reader = LengthReader(reader)
        self.writer = LengthWriter(writer)
        self.client_id = None
        self.db_name = None
        self.db_actions = None # can exist only after db_name is known
        self.directory = directory

        self.user_verified = False
        self.is_check_hash = False
        self.checked_state = False

        self.handlers = {
            InitConnActions.ADD_USER: Handler(self.handle_add_user, False),
            InitConnActions.ADD_PERMISSIONS: Handler(self.handle_add_permissions, False),
            InitConnActions.DB_INFO: Handler(self.handle_db_info, False),
            InitConnActions.CHECK_DB_HASH: Handler(self.handle_check_db_hash, False),
            InitConnActions.GET_DB_STATE: Handler(self.handle_get_db_state, True),
            InitConnActions.GET_DB: Handler(self.handle_get_db, True),
            InitConnActions.INIT_DONE: Handler(self.handle_init_done, False)
        }

        self.session_task = asyncio.create_task(self.handle_session())

    @validate_args_kwargs(['client_id'])
    def handle_add_user(self, *args, **kwargs):
        self.server.users.add_user(kwargs['client_id'])

    @validate_args_kwargs(['client_id', 'db_name'])
    def handle_add_permissions(self, *args, **kwargs):
        if not self.server.users.is_user_exists(kwargs['client_id']):
            logging.info(f"User {kwargs['client_id']} does not exists, adding it")
            self.server.users.add_user(kwargs['client_id'])

        self.server.users.add_db_permission(kwargs['client_id'], kwargs['db_name'])

    @validate_args_kwargs(['client_id', 'db_name'])
    def handle_db_info(self, *args, **kwargs):
        self.client_id = kwargs['client_id']
        self.db_name = kwargs['db_name']
        if not self.server.users.check_client_permissions(self.client_id, self.db_name):
            # TODO: make sure raise closes session and notify client
            logging.info("Client not allowed!")
            raise ClientNotAllowed()

        logging.info(f"Client {self.client_id} connected to db {self.db_name}")
        self.is_user_verified = True

    @validate_args_kwargs(['db_hash'])
    def handle_check_db_hash(self, *args, **kwargs):
        self.is_check_hash = self._check_db_md5(kwargs['db_hash'])

    async def handle_get_db_state(self, *args, **kwargs):
        message = md_pb2.InitConn(action_type=InitConnActions.GET_DB_STATE, state=self.is_check_hash)
        await self.send_protobuf(message)
        self.checked_state = True

    async def handle_get_db(self, *args, **kwargs):
        with open(os.path.join(self.directory, self.db_name), 'rb') as f:
            db_file = f.read()

        message = md_pb2.InitConn(action_type=InitConnActions.GET_DB, db_file=db_file)
        await self.send_protobuf(message)

    def handle_init_done(self, *args, **kwargs):
        logging.error("Client does not determine when init is done")

    async def _init_conn(self):
        while (not self.is_check_hash or not self.checked_state) or (not self.is_user_verified):
            message = md_pb2.InitConn()
            message.ParseFromString(await self.reader.read())
            logging.debug(f"init_conn {message.action_type}")

            kwargs = {k[0]: k[1]
                      for k in inspect.getmembers(message)
                      if not k[0].startswith('_') or not inspect.ismethod(k[1])}

            if message.action_type not in self.handlers.keys():
                raise InvalidAction(f"Unknonw action type: {message.action_type}")
            
            handler = self.handlers[message.action_type].handler
            is_async = self.handlers[message.action_type].is_async

            """
            Some of the handlers are sync function, but its fine because we are always
            context switching at the start of the while loop while reading from the client.
            Thus, we are not hogging the event loop
            """

            if is_async:
                await handler(**kwargs)
            else:
                handler(**kwargs)

    async def handle_session(self):
        await self._init_conn()
        self.db_actions = MDActions(self.server.directory, self.db_name, None)
        logging.debug("started handle session")
        while True:
            logging.debug("IN LOOP")
            request = await self.reader.read()
            logging.debug(f"Got request from server {request}")

            message = DBMessage(message_type=MessageTypes.DB_RESULT, 
                                db_result=DBResult(result=Results.SUCCESS))
            
            try:
                result = await self.db_actions.handle_protobuf(request)
                message.db_result.result_value = str(result)
            except Exception as e:
                message.db_result.result = EXCEPTIONS_TO_RESULT[type(e)]
            
            await self.send_protobuf(message)
            # TODO:
            # self.server.handle_session_request(self.db_name, request)

    def _check_db_md5(self, client_db_hash):
        db_hash = get_db_md5(os.path.join(self.directory, self.db_name))
        return client_db_hash == db_hash

    async def update_client(self, request):
        await self.send_protobuf(request)

    async def send_protobuf(self, protobuf):
        if isinstance(protobuf, (str, bytes)):
            # protobuf was already serialized
            await self.writer.write(protobuf)
        await self.writer.write(protobuf.SerializeToString())
