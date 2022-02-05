import asyncio
import logging

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s]: %(message)s")
LOGGER = logging.getLogger('md_logger')
LOGGER.setLevel(logging.DEBUG)


class Server(object):
    def __init__(self, logger: logging.Logger):
        self.sessions = {}
        self.db_sessions = {}
        self.logger = logger

    def handle_conn(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info('peername')
        self.logger.info(f"Got client connection from {peer}")

        # get md_client id and db name from protobuf
        client_id = None  # Should be something
        db_name = None  # Should be something

        # Verify that this md_client doesn't have active session already
        self.sessions[client_id] = Session(self, reader, writer, client_id, db_name)

        self.db_sessions.setdefault(db_name, []).append(self.sessions[client_id])

    def handle_session_request(self, db_name, request):
        for session in self.db_sessions[db_name]:
            session.update_client(request)


class Session(object):
    def __init__(self, server, reader, writer, client_id, db_name):
        self.server = server
        self.reader = reader
        self.writer = writer
        self.client_id = client_id
        self.db_name = db_name

        self.push_db()
        self.session_task = asyncio.create_task(self.handle_session())

    async def handle_session(self):
        while True:
            request = await self.reader.readuntil("\n") # use protobuf
            self.server.handle_session_request(self.db_name, request)

    def push_db(self):
        pass

    def update_client(self, request):
        self.writer.write(request)


async def main():
    s = Server(logger=LOGGER)
    server = await asyncio.start_server(
        s.handle_conn, '127.0.0.1', 8888)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
