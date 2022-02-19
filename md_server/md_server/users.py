from mdlib.db_utils import MDActions
from mdlib.exceptions import *

import logging


class DBUsers(object):
    def __init__(self, directory):
        self.db_name = 'users'
        self.directory = directory
        self.db_actions = MDActions(self.directory, self.db_name, channel=None)

    def add_user(self, client_id):
        # Verify username does not exist
        if self.is_user_exists(client_id):
            logging.error("Username already exist!")
            raise ClientIDAlreadyExists()

        logging.debug(f'User {client_id} was added!')
        self.db_actions.add_item(client_id, [])

    def is_user_exists(self, client_id: int):
        try:
            self.db_actions.get_key_value(client_id)
            return True
        except KeyDoesNotExists:
            return False

    def add_db_permission(self, client_id, db_name):
        if not self.is_user_exists(client_id):
            logging.error("User does not exist!")
            raise ClientIDDoesNotExist()
        elif db_name == self.db_name:
            logging.error("Client is never allowed to access user's db!")
            raise ClientNotAllowed()

        allowed_dbs = self.db_actions.get_key_value(client_id)
        if db_name not in allowed_dbs:
            logging.info(f"Allowing client {client_id} to access db {db_name}")
            allowed_dbs.append(db_name)
            self.db_actions.set_value(client_id, allowed_dbs)

    def check_client_permissions(self, client_id, db_name):
        user_exists = self.is_user_exists(client_id)
        if not user_exists:
            raise ClientIDDoesNotExist()

        allowed_dbs = self.db_actions.get_key_value(client_id)
        logging.error(f"Allowed dbs: {allowed_dbs}")

        if not isinstance(allowed_dbs, list):
            return False

        return db_name in allowed_dbs
