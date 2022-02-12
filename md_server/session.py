import asyncio
import logging
from mdlib import md_pb2
from mdlib.md_pb2 import InitConnActions
from mdlib.socket_utils import LengthReader, LengthWriter
from mdlib.db_utils import get_db_md5, MDActions
from mdlib.exceptions import *


class Session(object):
    def __init__(self, server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.server = server
        self.reader = LengthReader(reader)
        self.writer = LengthWriter(writer)
        self.client_id = None
        self.db_name = None
        self.db_actions = None  # can exist only after db_name is known

        self.session_task = asyncio.create_task(self.handle_session())

    async def _init_conn(self):
        is_user_verified = False
        is_check_hash = False
        while (not is_check_hash) or (not is_user_verified):
            message = md_pb2.InitConn()
            message.ParseFromString(await self.reader.read())
            logging.debug(f"init_conn {message.action_type}")
            match message.action_type:
                case InitConnActions.ADD_USER:
                    self.server.users.add_user(message.client_id)
                    break
                case InitConnActions.ADD_PERMISSIONS:
                    self.server.users.add_db_permission(message.client_id, message.db_name)
                    break
                case InitConnActions.DB_INFO:
                    self.client_id = message.client_id
                    self.db_name = message.db_name
                    if not self.server.users.check_client_permissions(self.client_id, self.db_name):
                        # TODO: make sure raise closes session and notify client
                        logging.info(f"Client not allowed!")
                        raise ClientNotAllowed()
                    logging.info(f"Client {self.client_id} connected to db {self.db_name}")
                    is_user_verified = True
                    break
                case InitConnActions.CHECK_DB_HASH:
                    is_check_hash = self._check_db_md5(message.db_hash)
                    break
                case InitConnActions.GET_DB_STATE:
                    message = md_pb2.InitConn(action_type=InitConnActions.GET_DB_STATE, state=is_check_hash)
                    await self.writer.write(message)
                    break
                case InitConnActions.GET_DB:
                    with open(self.db_name, 'rb') as f:
                        db_file = f.read()
                    message = md_pb2.InitConn(action_type=InitConnActions.GET_DB, db_file=db_file)
                    await self.writer.write(message)
                    break
                case InitConnActions.INIT_DONE:
                    logging.error("Client does not determine when init is done")
                    break
                case _:
                    raise InvalidAction()



    async def handle_session(self):
        await self._init_conn()
        self.db_actions = MDActions(self.server.directory, self.db_name)
        logging.debug("started handle session")
        while True:
            logging.debug("IN LOOP")
            request = await self.reader.read()
            logging.debug(f"Got request from server {request}")
            self.db_actions.handle_protobuf(request)
            self.server.handle_session_request(self.db_name, request)

    async def _check_db_md5(self, client_db_hash):
        db_hash = get_db_md5(self.db_name)
        return client_db_hash == db_hash

    async def update_client(self, request):
        await self.writer.write(request)
