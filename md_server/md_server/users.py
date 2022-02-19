from mdlib.db_utils import MDActions
from mdlib.exceptions import *

import logging


class DBUsers(object):
    def __init__(self, directory):
        self.db_name = 'users'
        self.directory = directory
        self.db_actions = MDActions(self.directory, self.db_name, channel=None)

    def get_client_info(self, client_id):
        try:
            client_info = self.db_actions.get_key_value(client_id)
        except KeyDoesNotExists:
            raise ClientIDDoesNotExist()

        return client_info

    def is_admin(self, client_id):
        return self.get_client_info['is_admin']

    def is_correct_password(self, client_id, password):
        return self.get_client_info(client_id)['password'] == password

    def add_user(self, client_id, password):
        try:
            client_info = self.get_client_info(client_id)
            logging.error(f"Client ID {client_id} already exist!")
            raise ClientIDAlreadyExists()
        except ClientIDDoesNotExist:
            # The user doesn not exists, add it
            logging.info(f"Adding user {client_id}!")
            self.db_actions.add_item(client_id, {
                'password': password,
                'is_admin': False,
                'allowed_dbs': []
            })
            logging.debug(f'User {client_id} was added!')

    def is_user_exists(self, client_id: int) -> bool:
        try:
            self.get_client_info(client_id)
            return True
        except ClientIDDoesNotExist:
            return False

    def add_db_permission(self, client_id, db_name):
        if db_name == self.db_name:
            logging.error("Clients is never allowed to access user's db!")
            raise ClientNotAllowed()

        client_info = self.get_client_info(client_id)
        if db_name not in client_info['allowed_dbs']:
            logging.info(f"Allowing client {client_id} to access db {db_name}")
            client_info['allowed_dbs'].append(db_name)
            self.db_actions.set_value(client_id, client_info)
        else:
            logging.info(f"Client {client_id} already has access to {db_name}")

    def check_client_permissions(self, client_id, db_name):
        allowed_dbs = self.get_client_info(client_id)['allowed_dbs']
        if not isinstance(allowed_dbs, list):
            return False

        return db_name in allowed_dbs
