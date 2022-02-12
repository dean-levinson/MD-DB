import os
import json
import hashlib
import logging
import functools
from mdlib.md_pb2 import DBAction, Actions

class MDActions(object):
    """
    for md_client - After receive protobuf from md_server, change the db accordingly.
    for md_server - Change the local db.
    """

    def __init__(self, db_directory, db_name, is_client=False):
        self.db_directory = db_directory
        self.db_name = db_name
        self.db_path = os.path.join(self.db_directory, self.db_name)
        self.is_client = is_client

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
        action = DBAction()
        action.ParseFromString(protobuf_obj)
        match action.action_type:
            case Actions.ADD_ITEM:
                self.add_item(key=action.key, value=action.value)
            case Actions.SET_VALUE:
                self.set_value(key=action.key, value=action.value)
            case Actions.DELETE_KEY:
                self.delete_key(key=action.key)
            case Actions.DELETE_DB:
                self.delete_db()

    def _get_client_request(self, action_type, key=None, value=None):
        action = DBAction()
        if action_type is None:
            raise NotImplementedError("Client didn't choose action!")
        action.action_type = action_type
        if key is not None:
            action.key = key
        if value is not None:
            action.value = value
        return action.SerializeToString()

    # todo: Consider delete this
    def __enter__(self):
        with open(self.db_path, 'r') as db_descriptor:
            self._tmp_db_dict = json.load(db_descriptor)
        return self._tmp_db_dict

    # todo: Consider delete this
    def __exit__(self, exc_type, exc_value, traceback):
        if traceback:
            logging.exception(traceback)
        if exc_type:
            raise exc_type(exc_value)

        with open(self.db_path, 'w') as db_descriptor:
            json.dump(self._tmp_db_dict, db_descriptor)

    def db_transaction(write_to_db=True, action_type=None):
        def deco(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                if self.is_client:
                    return self._get_client_request(action_type, *args)
                with open(self.db_path, 'r') as db_descriptor:
                    self.db_data = json.load(db_descriptor)

                ret_val = func(self, *args, **kwargs)

                if write_to_db:
                    with open(self.db_path, 'w') as db_descriptor:
                        json.dump(self.db_data, db_descriptor)
                    logging.debug(f"Updated db! {self.db_data}")

                return ret_val
            return wrapper
        return deco

    @db_transaction(write_to_db=True, action_type=Actions.ADD_ITEM)
    def add_item(self, key, value=None):
        key = str(key)
        if key in self.db_data:
            logging.error(f"{key} already exist in DB '{self.db_path}'")
            raise KeyError(f"{key} already exist in DB '{self.db_path}'")
        self.db_data[key] = value

    @db_transaction(write_to_db=True, action_type=Actions.SET_VALUE)
    def set_value(self, key, value):
        key = str(key)
        self.db_data[key] = value

    @db_transaction(write_to_db=False)
    def get_key_value(self, key):
        key = str(key)
        return self.db_data[key]

    @db_transaction(write_to_db=True, action_type=Actions.DELETE_KEY)
    def delete_key(self, key):
        key = str(key)
        if key not in self.db_data:
            raise KeyError(f"{key} not in DB '{self.db_path}'")

        del self.db_data[key]

    def delete_db(self):
        # Delete db from local
        # Delete db from all related clients?
        # Close all related connections gracefully
        pass

def get_db_md5(db_name):
    with open(db_name, 'rb') as db:
        data = db.read()
    return hashlib.md5(data).hexdigest()
