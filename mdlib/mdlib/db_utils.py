import os
import asyncio
import json
import hashlib
import logging
import functools
from mdlib.md_pb2 import DBAction, Actions, DBMessage, MessageTypes, Results
from mdlib.exceptions import *

RESULTS_TO_EXCEPTIONS = {
    Results.SUCCESS: None,
    Results.KEY_DOES_NOT_EXISTS: KeyDoesNotExists,
    Results.KEY_ALREADY_EXISTS: KeyAlreadyExists
}
        
EXCEPTIONS_TO_RESULT = {v: k for k, v in RESULTS_TO_EXCEPTIONS.items()}

class MDActions(object):
    """
    for md_client - After receive protobuf from md_server, change the db accordingly.
    for md_server - Change the local db.
    """

    def __init__(self, db_directory, db_name, channel=None, is_client=False):
        self.db_directory = db_directory
        self.db_name = db_name
        self.db_path = os.path.join(self.db_directory, self.db_name)
        self.is_client = is_client
        self.channel: asyncio.Queue = channel

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

    async def handle_protobuf(self, protobuf_obj):
        message = DBMessage()
        message.ParseFromString(protobuf_obj)

        if message.message_type == MessageTypes.DB_ACTION:
            action = message.db_action
            match action.action_type:
                case Actions.ADD_ITEM:
                    self.add_item(key=action.key, value=action.value)
                case Actions.SET_VALUE:
                    self.set_value(key=action.key, value=action.value)
                case Actions.GET_KEY_VALUE:
                    return self.get_key_value(key=action.key)
                case Actions.GET_ALL_KEYS:
                    return self.get_all_keys()
                case Actions.DELETE_KEY:
                    self.delete_key(key=action.key)
                case Actions.DELETE_DB:
                    self.delete_db()

        elif message.message_type == MessageTypes.DB_RESULT:
            logging.info(f"Result of last operation: {message.db_result.result}")
            if self.channel is not None:
                await self.channel.put(message.db_result)
            

    def _get_client_request(self, action_type, key=None, value=None):
        message = DBMessage()
        if action_type is None:
            raise InvalidAction()

        message.message_type = MessageTypes.DB_ACTION
        message.db_action.action_type = action_type
        if key is not None:
            message.db_action.key = key
        if value is not None:
            message.db_action.value = value
        return message.SerializeToString()

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
            raise KeyAlreadyExists()
        self.db_data[key] = value

    @db_transaction(write_to_db=True, action_type=Actions.SET_VALUE)
    def set_value(self, key, value):
        key = str(key)
        self.db_data[key] = value

    @db_transaction(write_to_db=False, action_type=Actions.GET_KEY_VALUE)
    def get_key_value(self, key):
        key = str(key)
        if key not in self.db_data.keys():
            return None
        return self.db_data[key]

    @db_transaction(write_to_db=False, action_type=Actions.GET_ALL_KEYS)
    def get_all_keys(self):
        # Returns an array of all keys in db
        return list(self.db_data.keys())


    @db_transaction(write_to_db=True, action_type=Actions.DELETE_KEY)
    def delete_key(self, key):
        key = str(key)
        if key not in self.db_data:
            raise KeyDoesNotExists()

        del self.db_data[key]

    @db_transaction(write_to_db=False, action_type=Actions.DELETE_DB)
    def delete_db(self):
        logging.info(f'deleting db {self.db_path}!')
        os.remove(self.db_path)
        if self.is_client:
            # TODO: close client's connection to sever somehow
            pass

def get_db_md5(db_name):
    logging.info(f"dbname: {db_name}")
    with open(db_name, 'rb') as db:
        data = db.read()
    return hashlib.md5(data).hexdigest()
