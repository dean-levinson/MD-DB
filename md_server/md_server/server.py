import asyncio
import logging
import traceback
from collections import namedtuple

from md_server.session import Session
from md_server.users import DBUsers

AddAdminUserParams = namedtuple("AddAdminUserParams", ["should_add", "client_id", "password"])

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s]: %(message)s")


class Server(object):
    def __init__(self, directory, add_admin_params):
        self.db_sessions = {}
        self.directory = directory
        self.users = DBUsers(self.directory, add_admin_params)

    async def handle_conn(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handles every new connection the server gets.
        For each new connection a Session object is initialized.
        """
        peer = writer.get_extra_info('peername')
        logging.info(f"Got client connection from {peer}")
        session = Session(self, reader, writer, self.directory, self.db_sessions)
        try:
            await session.handle_session()
        except Exception as e:
            logging.error(f"Got Exception on {session}! closing session...\n{traceback.format_exc()}")
            writer.close()
            await writer.wait_closed()
        finally:
            logging.info(f"Client {session.client_id} was disconnected")
            if session.is_user_verified:
                self.db_sessions[session.db_name].remove(session)
                if len(self.db_sessions[session.db_name]) == 0:
                    self.db_sessions.pop(session.db_name)

    async def handle_session_request(self, db_name: str, request):
        """
        Updates all the clients that are connected to db `dbnanme` with the request.
        This will allow the clients to update their local dbs.
        @param str db_name: The name of the db the request is related to.
        @param request: The protobuf that will be sent to all relevant clients.
        """

        # Update local clients dbs
        logging.info(f"Updating all clients connected to {db_name}")
        for session in self.db_sessions[db_name]:
            await session.update_client(request)
