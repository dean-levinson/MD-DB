import asyncio
import logging

from md_server.session import Session


class Server(object):
    def __init__(self):
        self.sessions = {}
        self.db_sessions = {}

    def handle_conn(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info('peername')
        logging.info(f"Got client connection from {peer}")

        # get md_client id and db name from protobuf
        client_id = None  # Should be something
        db_name = "mydb2"  # Should be something

        # Verify that this md_client doesn't have active session already
        self.sessions[client_id] = Session(self, reader, writer, client_id, db_name)

        self.db_sessions.setdefault(db_name, []).append(self.sessions[client_id])

    def handle_session_request(self, db_name, request):
        for session in self.db_sessions[db_name]:
            session.update_client(request)
