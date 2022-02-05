import asyncio
import logging
from mdlib import md_pb2
from mdlib.socket_utils import LengthReader, LengthWriter
from mdlib.db_utils import get_db_md5


class Session(object):
    def __init__(self, server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_id, db_name):
        self.server = server
        self.reader = LengthReader(reader)
        self.writer = LengthWriter(writer)
        self.client_id = client_id
        self.db_name = db_name

        self.session_task = asyncio.create_task(self.handle_session())

    async def handle_session(self):
        await self.push_db()
        while True:
            request = await self.reader.read()
            logging.debug(f"Got request from server {request}")
            self.server.handle_session_request(self.db_name, request)

    async def push_db(self):
        db_hash = get_db_md5(self.db_name)
        client_db_hash = md_pb2.GetDBHash()
        client_db_hash.ParseFromString(await self.reader.read())
        db_state = md_pb2.GetDBState()
        logging.debug(f"client: {client_db_hash}")
        if client_db_hash.db_hash != db_hash:
            logging.info("Dbs not synced!")
            db_state.state = md_pb2.DBState.NOT_SYNCED
            data = db_state.SerializeToString()
            logging.debug(data)
            logging.debug(f"LENGTH{len(data)}")

            self.writer.write(data)
            print("saa")
            with open(self.db_name, 'rb') as f:
                db_file = f.read()
            message = md_pb2.GetDB(db_file=db_file)
            print("HERE")
            self.writer.write(message.SerializeToString())
        else:
            db_state.state = md_pb2.DBState.SYNCED
            self.writer.write(db_state.SerializeToString())

    def update_client(self, request):
        self.writer.write(request)
