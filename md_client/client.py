from mdlib.db_utils import MDActions, MDProtocol

import asyncio
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

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.hostname, 8888)

        # send protobuf of self.client_id, self.db_name
        self.pull_db()
        self.sync_task = asyncio.create_task(self.sync_with_remote())

    async def sync_with_remote(self):
        while True:
            if self.reader:
                action = await self.reader.read()
                self.db_actions.handle_protobuf(action)

    def pull_db(self):
        pass

    def send_protobuf(self, protobuf):
        self.logger.debug(f"Sent protobuf {protobuf}")
        self.writer.write(protobuf)

    def add_item(self, item):
        pass
        # message = self.md_protocol.create_message(ADD, paten)
        # self.send_protobuf(message)

    def delete_item(self, item):
        pass
