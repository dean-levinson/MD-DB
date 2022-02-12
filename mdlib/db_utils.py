import os
import json
import hashlib
import logging
from mdlib.md_pb2 import DBAction, Actions


class MDActions(object):
    """
    for md_client - After receive protobuf from md_server, change the db accordingly.
    for md_server - Change the local db.
    """

    def __init__(self, db_directory, db_name):
        self.db_directory = db_directory
        self.db_name = db_name
        self.db_path = os.path.join(self.db_directory, self.db_name)

        self.db_data = {}
        self.load_db_data()

    def load_db_data(self):
        if not os.path.exists(self.db_path):
            logging.info(f"Requested db {self.db_path} doesn't exist! Creating a new empty db.")
            self.create_db()
        with open(self.db_path, 'rb') as db_descriptor:
            self.db_data = json.load(db_descriptor)

    def create_db(self):
        # No need to update other client because this is a new db
        with open(self.db_path, 'w') as db_descriptor:
            json.dump({}, db_descriptor)

    def handle_protobuf(self, protobuf_obj):
        # call DBProtocol to parse obj
        # call switch case
        action = DBAction()
        action.ParseFromString(protobuf_obj)
        match action:
            case Actions.ADD_ITEM:
                self.add_item(key=action.key, value=action.value)
            case Actions.SET_VALUE:
                self.set_value(key=action.key, value=action.value)
            case Actions.DELETE_KEY:
                self.delete_key(key=action.key)
            case Actions.DELETE_DB:
                self.delete_db()

    def add_item(self, key, value=None):
        pass

    def set_value(self, key, value):
        pass

    def get_key_value(self, key):
        pass

    def delete_key(self, key):
        pass

    def delete_db(self):
        # Delete db from local
        # Delete db from all related clients?
        # Close all related connections gracefully
        pass


class MDProtocol(object):
    KEYS = {
        "add": 1,
        "delete": 2
    }

    def __init__(self):
        pass

    def create_message(self, action, key, value=None):
        # protobuf.pasten()
        pass


def get_db_md5(db_name):
    with open(db_name, 'rb') as db:
        data = db.read()
    return hashlib.md5(data).hexdigest()
