import os
import asyncio
import inspect
import logging
import traceback
import functools
from collections import namedtuple

from mdlib import md_pb2
from mdlib.exceptions import InvalidAction
from mdlib.md_pb2 import InitConn, InitConnActions, Results, DBResult
from mdlib.md_pb2 import DBMessage, MessageTypes, Results
from mdlib.socket_utils import LengthReader, LengthWriter
from mdlib.db_utils import get_db_md5, MDActions, EXCEPTIONS_TO_RESULT
from mdlib.exceptions import *

Handler = namedtuple("Handler", ["handler", "is_async"])


def validate_args_kwargs(arguments):
    """
    Makes sure all the args that must exist to use the function are in kwargs.
    """
    def decorator(func):
        def validator(*args, **kwargs):
            for arg in arguments:
                if arg not in kwargs.keys():
                    raise ValueError("{arg} must be in kwargs")

            return func(*args, **kwargs)

        return validator

    return decorator


class Session(object):
    def __init__(self, server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, directory: str,
                 db_sessions: dict):
        self.server = server
        self.reader = LengthReader(reader)
        self.writer = LengthWriter(writer)
        self.client_id = None
        self.db_name = None
        self.db_actions = None  # can exist only after db_name is known
        self.directory = directory
        self.server_db_sessions = db_sessions

        self.is_user_verified = False
        self.is_check_hash = False
        self.checked_state = False

        self.handlers = {
            InitConnActions.LOGIN: Handler(self.handle_login, True),
            InitConnActions.ADD_USER: Handler(self.handle_add_user, True),
            InitConnActions.CHECK_DB_HASH: Handler(self.handle_check_db_hash, False),
            InitConnActions.GET_DB_STATE: Handler(self.handle_get_db_state, True),
            InitConnActions.GET_DB: Handler(self.handle_get_db, True),
        }

    @validate_args_kwargs(['client_id', 'password', 'db_name'])
    async def handle_login(self, *args, **kwargs):
        """
        Handles the client's login to the server.
        """
        client_id = kwargs['client_id']
        db_name = kwargs['db_name']
        password = kwargs['password']
        logging.info(f"Got login request from {client_id} to {db_name}")

        self.client_id = client_id
        self.db_name = db_name

        message = md_pb2.DBResult()
        try:
            if self.server.users.is_correct_password(client_id, password):
                if self.server.users.check_client_permissions(self.client_id, self.db_name):
                    logging.info(f"Client {self.client_id} connected successfully to db {self.db_name}")
                    self.is_user_verified = True
                    self.server_db_sessions.setdefault(self.db_name, []).append(self)
                    message.result = Results.SUCCESS

                    # initialize db_actions now because session has all relevant details and had validated them
                    self.db_actions = MDActions(self.server.directory, self.db_name, None)
                else:
                    logging.info(f"Client {self.client_id} is not allowed to access {self.db_name}")
                    message.result = Results.USER_NOT_ALLOWED
            else:
                message.result = Results.INCORRECT_PASSWORD
                logging.info(f"Client {self.client_id} passed incorrect password!")
        except ClientIDDoesNotExist:
            message.result = Results.USER_DOES_NOT_EXISTS

        await self.send_protobuf(message)

    @validate_args_kwargs(['client_id', 'password'])
    async def handle_add_user(self, *args, **kwargs):
        """
        Adds the client's user and password to the server's users.
        """
        message = md_pb2.DBResult()
        try:
            self.server.users.add_user(kwargs['client_id'], kwargs['password'])
            message.result = Results.SUCCESS
        except Exception as e:
            message.result = EXCEPTIONS_TO_RESULT[type(e)]

        await self.send_protobuf(message)

    @validate_args_kwargs(['db_hash'])
    def handle_check_db_hash(self, *args, **kwargs):
        """
        Checks if the client's db's hash is like the servers.
        """
        self.is_check_hash = self._check_db_md5(kwargs['db_hash'])
        # todo: do we need the line below?
        # self.checked_state = False

    async def handle_get_db_state(self, *args, **kwargs):
        """
        Sends a message to the client that indicates whether the server's and client's dbs are synced or not.
        """
        message = md_pb2.InitConn(action_type=InitConnActions.GET_DB_STATE, state=self.is_check_hash)
        await self.send_protobuf(message)
        self.checked_state = True

    async def handle_get_db(self, *args, **kwargs):
        """
        Sends the client the entire db, because they are probably not synced.
        """
        with open(os.path.join(self.directory, self.db_name), 'rb') as f:
            db_file = f.read()

        message = md_pb2.InitConn(action_type=InitConnActions.GET_DB, db_file=db_file)
        await self.send_protobuf(message)

    async def _init_conn(self):
        """
        Handles the initialization of the connection to the clients.
        Verifies the user is allowed to login, that the dbs are synced and
        """
        while (not self.is_check_hash or
               not self.checked_state or
               not self.is_user_verified):

            message = md_pb2.InitConn()
            message.ParseFromString(await self.reader.read())

            kwargs = {k[0]: k[1]
                      for k in inspect.getmembers(message)
                      if not k[0].startswith('_') or not inspect.ismethod(k[1])}

            if message.action_type not in self.handlers.keys():
                raise InvalidAction(f"Unknown action type: {message.action_type}")

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
        """
        The main functions that runs the client's session.
        Does initialization actions, then starts the main loop that is waiting for messages
        from the client.
        """
        await self._init_conn()

        while True:
            request = await self.reader.read()
            logging.debug(f"{self} got request from client")
            message = DBMessage(message_type=MessageTypes.DB_RESULT,
                                db_result=DBResult(result=Results.SUCCESS))

            try:
                result = await self.db_actions.handle_protobuf(request)
                logging.debug(f"Result is: {result}")
            except Exception as e:
                logging.error(f"Got Exception on {self} while handling a request!\n{traceback.format_exc()}")
                message.db_result.result = EXCEPTIONS_TO_RESULT[type(e)]

            if result is not None:
                message.db_value.value_type, message.db_value.value = result
            else:
                # If result is none, command was to update something in DB. Notify all relevant clients.
                await self.server.handle_session_request(self.db_name, bytes(request))
            # send our client the response message
            await self.send_protobuf(message)

    def _check_db_md5(self, client_db_hash:str):
        """
        Checks if the client's db's hash is the same as the server's.
        """
        db_hash = get_db_md5(self.db_path)
        return client_db_hash == db_hash

    async def update_client(self, request):
        """
        Send the request to the client.
        @param request: Protobuf message for the client.
        """
        await self.send_protobuf(request)

    async def send_protobuf(self, protobuf):
        """
        Sends the protobuf to the client.
        @param protobuf: protobuf can be serialized or not.
        """
        if isinstance(protobuf, (str, bytes, bytearray)):
            # protobuf was already serialized
            await self.writer.write(protobuf)
        else:
            await self.writer.write(protobuf.SerializeToString())

    @property
    def db_path(self):
        """
        The path to the directory in which the server will save the dbs.
        """
        if self.directory and self.db_name:
            return os.path.join(self.directory, self.db_name)
        else:
            return self.db_name

    def __str__(self):
        return f"Session(sever={self.server}, client_id={self.client_id}, db_path={self.db_path})"
