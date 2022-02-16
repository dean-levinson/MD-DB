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
        logging.debug("HERE1")
        if self.db_actions.get_key_value(client_id) is not None:
            logging.error("Username already exist!")
            raise ClientIDAlreadyExists()
        logging.debug(f'User {client_id} was added!')
        self.db_actions.add_item(client_id, [])

    def is_user_exists(self, client_id: int):
        return self.db_actions.get_key_value(client_id) is not None

    def add_db_permission(self, client_id, db_name):
        assert db_name != self.db_name, "Client is never allowed to access server!"
        allowed_dbs = self.db_actions.get_key_value(client_id)
        if db_name not in allowed_dbs:
            logging.debug(f"Allowing client {client_id} to access db {db_name}")
            allowed_dbs.append(db_name)
            self.db_actions.set_value(client_id, allowed_dbs)

    def check_client_permissions(self, client_id, db_name):
        allowed_dbs = self.db_actions.get_key_value(client_id)
        logging.debug("HERE1")
        if not isinstance(allowed_dbs, list):
            return False
        logging.debug("HERE2")
        logging.debug(allowed_dbs)
        return db_name in allowed_dbs
