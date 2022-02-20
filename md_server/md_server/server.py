import asyncio
import logging
import traceback

from md_server.session import Session
from md_server.users import DBUsers

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s]: %(message)s")


class Server(object):
    def __init__(self, directory, add_admin_params):
        self.sessions = {}
        self.db_sessions = {}
        self.directory = directory
        self.users = DBUsers(self.directory, add_admin_params)

    async def handle_conn(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info('peername')
        logging.info(f"Got client connection from {peer}")
        session = Session(self, reader, writer, self.directory, self.sessions, 
                          self.db_sessions)
        # TODO: Add support of 2 client_ids to 2 different dbs
        # TODO: Verify that this md_client doesn't have active session already

        try:
            await session.handle_session()
        except Exception as e:
            logging.error(f"Got Exception on {session}! closing session...\n{traceback.format_exc()}")
            writer.close()
            await writer.wait_closed()
        finally:
            logging.info(f"Client {session.client_id} was disconnected")
            if session.is_user_verified:
                self.sessions.pop(session.client_id)
                self.db_sessions[session.db_name].remove(session)
                if len(self.db_sessions[session.db_name]) == 0:
                    self.db_sessions.pop(session.db_name)

    async def handle_session_request(self, db_name, request):
        # Local db was updated in Session

        # Update other clients dbs
        logging.debug(f"Updating {db_name} on all clients")
        for session in self.db_sessions[db_name]:
            await session.update_client(request)
