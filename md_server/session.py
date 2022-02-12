import asyncio
import logging
from mdlib import md_pb2
from mdlib.socket_utils import LengthReader, LengthWriter
from mdlib.db_utils import get_db_md5, MDActions


class Session(object):
    def __init__(self, server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.server = server
        self.reader = LengthReader(reader)
        self.writer = LengthWriter(writer)
        self.client_id = None
        self.db_name = None
        self.db_actions = None  # can exist only after db_name is known

        self.session_task = asyncio.create_task(self.handle_session())

    async def handle_session(self):
        await self.get_db_info()
        await self.push_db()
        self.db_actions = MDActions(self.server.directory, self.db_name)
        logging.debug("started handle session")
        while True:
            logging.debug("IN LOOP")
            request = await self.reader.read()
            logging.debug(f"Got request from server {request}")
            self.db_actions.handle_protobuf(request)
            self.server.handle_session_request(self.db_name, request)

    async def get_db_info(self):
        db_info = md_pb2.DBInfo()
        db_info.ParseFromString(await self.reader.read())
        self.client_id = db_info.client_id
        self.db_name = db_info.db_name
        logging.info(f"Client {self.client_id} connected to db {self.db_name}")

    async def push_db(self):
        db_hash = get_db_md5(self.db_name)

        client_db_hash = md_pb2.GetDBHash()
        client_db_hash.ParseFromString(await self.reader.read())

        db_state = md_pb2.GetDBState()
        if client_db_hash.db_hash != db_hash:
            logging.info("Dbs not synced!")
            db_state.state = md_pb2.DBState.NOT_SYNCED
            data = db_state.SerializeToString()
            await self.writer.write(data)
            with open(self.db_name, 'rb') as f:
                db_file = f.read()
            message = md_pb2.GetDB(db_file=db_file)
            await self.writer.write(message.SerializeToString())
        else:
            logging.info("Dbs are already synced!")
            db_state.state = md_pb2.DBState.SYNCED
            await self.writer.write(db_state.SerializeToString())

    async def update_client(self, request):
        await self.writer.write(request)
