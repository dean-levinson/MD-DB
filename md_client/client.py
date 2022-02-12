from mdlib.socket_utils import LengthReader, LengthWriter
from mdlib.db_utils import MDActions, get_db_md5
from mdlib.exceptions import *
from mdlib import md_pb2

import asyncio
import logging
from typing import Optional


class Client(object):
    def __init__(self, hostname, db_name, client_id, db_directory=None):
        self.reader = None  # type: Optional[LengthReader]
        self.writer = None  # type: Optional[LengthWriter]
        self.hostname = hostname
        self.db_name = db_name
        self.client_id = client_id
        self.db_directory = db_directory
        self.db_actions = MDActions(db_directory, db_name, is_client=True)
        self.sync_task = None
        self._is_connected = False

    async def connect(self):
        if self._is_connected:
            raise AlreadyConnected()

        reader, writer = await asyncio.open_connection(
            self.hostname, 8888)
        self.reader = LengthReader(reader)
        self.writer = LengthWriter(writer)

        await self.send_db_info()
        await self.pull_db()
        self.sync_task = asyncio.create_task(self._sync_with_remote())

        self._is_connected = True

    async def _sync_with_remote(self):
        while True:
            if self.reader:
                action = await self.reader.read()
                logging.debug(f'client {self.client_id} got action from server')
                self.db_actions.handle_protobuf(action)

    async def send_db_info(self):
        message = md_pb2.DBInfo(db_name=self.db_name, client_id=self.client_id)
        await self.writer.write(message.SerializeToString())

    async def pull_db(self):
        db_hash = get_db_md5(self.db_name)
        message = md_pb2.GetDBHash(db_hash=db_hash)
        await self.writer.write(message.SerializeToString())

        db_state = md_pb2.GetDBState()
        db_state.ParseFromString(await self.reader.read())

        if db_state.state == md_pb2.DBState.NOT_SYNCED:
            logging.info("DBs are not synced! Syncing dbs, this might overwrite data")
            db_data = md_pb2.GetDB()
            db_data.ParseFromString(await self.reader.read())
            with open(self.db_name, 'wb') as f:
                f.write(db_data.db_file)
