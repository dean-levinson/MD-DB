import asyncio
import logging


class Session(object):
    def __init__(self, server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_id, db_name):
        self.server = server
        self.reader = reader
        self.writer = writer
        self.client_id = client_id
        self.db_name = db_name

        self.push_db()
        self.session_task = asyncio.create_task(self.handle_session())

    async def handle_session(self):
        while True:
            request = await self.reader.read(2)  # Somehow should know how much to read
            logging.debug(f"Got request from server {request}")
            self.server.handle_session_request(self.db_name, request)

    def push_db(self):
        pass

    def update_client(self, request):
        self.writer.write(request)
