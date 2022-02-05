from mdlib.db_utils import MDActions, MDProtocol
from mdlib.socket_utils import LengthReader, LengthWriter
from md_client.exceptions import *
from mdlib.db_utils import get_db_md5
from mdlib import md_pb2

import asyncio
import logging
from typing import Optional


class Client(object):
    def __init__(self, hostname, db_name, db_directory=None):
        self.reader = None  # type: Optional[asyncio.StreamReader]
        self.writer = None  # type: Optional[asyncio.StreamWriter]
        self.hostname = hostname
        self.db_name = db_name
        self.db_directory = db_directory
        self.db_actions = MDActions(db_directory, db_name)
        self.sync_task = None
        self._is_connected = False

    async def connect(self):
        if self._is_connected:
            raise AlreadyConnected()

        reader, writer = await asyncio.open_connection(
            self.hostname, 8888)
        self.reader = LengthReader(reader)
        self.writer = LengthWriter(writer)

        # send protobuf of self.client_id, self.db_name
        await self.pull_db()
        self.sync_task = asyncio.create_task(self.sync_with_remote())

        self._is_connected = True

    async def sync_with_remote(self):
        while True:
            if self.reader:
                action = await self.reader.read()
                self.db_actions.handle_protobuf(action)

    async def pull_db(self):
        db_hash = get_db_md5(self.db_name)
        message = md_pb2.GetDBHash(db_hash=db_hash)
        self.writer.write(message.SerializeToString(message))
        db_state = md_pb2.GetDBState()
        db_state.ParseFromString(await self.reader.read())
        if db_state.state == md_pb2.DBState.NOT_SYNCED:
            logging.info("DBs are not synced! Syncing dbs, this might overwrite data")
            db_data = md_pb2.GetDB()
            db_data.ParseFromString(await self.reader.read())
            with open(self.db_name, 'wb') as f:
                f.write(db_data.db_file)


def send_protobuf(self, protobuf):
    logging.debug(f"Sent protobuf {protobuf}")
    self.writer.write(protobuf)


def add_item(self, item):
    pass
    # message = self.md_protocol.create_message(ADD, paten)
    # self.send_protobuf(message)


def delete_item(self, item):
    pass
