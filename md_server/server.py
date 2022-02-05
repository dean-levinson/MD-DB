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
        session = Session(self, reader, writer)
        # Verify that this md_client doesn't have active session already
        self.sessions[session.client_id] = session
        self.db_sessions.setdefault(session.db_name, []).append(self.sessions[session.client_id])

    def handle_session_request(self, db_name, request):
        for session in self.db_sessions[db_name]:
            session.update_client(request)
