import os
import functools
from mdlib.socket_utils import LengthReader, LengthWriter
from mdlib.db_utils import MDActions, get_db_md5, RESULTS_TO_EXCEPTIONS
from mdlib.exceptions import *
from mdlib import md_pb2
from mdlib.md_pb2 import InitConnActions, Results, DBResult

import asyncio
import logging
from typing import Optional


class Client(object):
    def __init__(self, addr, db_name, client_id, password, channel: asyncio.Queue = None, db_directory=None):
        self.reader: Optional[LengthReader] = None
        self.writer: Optional[LengthWriter] = None
        self.hostname, self.port = addr
        self.db_name = db_name
        self.client_id = client_id
        self.password = password
        self.db_directory = db_directory or '.'
        self.channel: asyncio.Queue = channel
        self.db_actions = MDActions(db_directory, db_name, self.channel, is_client=True)
        self.sync_task = None
        self._is_connected = False
        self.pulled_db = False

    async def connect(self, add_user=False):
        if self._is_connected:
            raise AlreadyConnected()

        reader, writer = await asyncio.open_connection(
            self.hostname, self.port)
        self.reader = LengthReader(reader)
        self.writer = LengthWriter(writer)

        await self._init_conn(add_user)
        self._is_connected = True
        return True

    async def disconnect(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def sync_with_remote(self):
        try:
            while True:
                if self.reader:
                    action = await self.reader.read()
                    logging.debug(f'client {self.client_id} got action from server')
                    await self.db_actions.handle_protobuf(action)
        except (asyncio.CancelledError, Exception) as e:
            pass

    async def login(self):
        message = md_pb2.InitConn(action_type=InitConnActions.LOGIN, 
                                  client_id=self.client_id, 
                                  db_name=self.db_name,
                                  password=self.password)

        await self.send_protobuf(message)
        await self.__get_init_conn_result()

    async def _init_conn(self, add_user=False):
        if add_user:
            await self._add_user()

        await self.login()
        await self.pull_db()

    async def _add_user(self):
        message = md_pb2.InitConn(action_type=InitConnActions.ADD_USER, 
                                  client_id=self.client_id,
                                  password=self.password)

        await self.send_protobuf(message)
        await self.__get_init_conn_result()

    async def _check_hash(self, db_hash):
        message = md_pb2.InitConn(action_type=InitConnActions.CHECK_DB_HASH, db_hash=db_hash)
        await self.send_protobuf(message)
        message = md_pb2.InitConn(action_type=InitConnActions.GET_DB_STATE)
        await self.send_protobuf(message)

        message = md_pb2.InitConn()
        data = await self.reader.read()
        message.ParseFromString(data)
        if not message.action_type == InitConnActions.GET_DB_STATE:
            logging.info(f"message: {data}")
            raise UnexpectedAction()
        return message.state

    async def pull_db(self):
        db_path = os.path.join(self.db_directory, self.db_name)
        db_hash = get_db_md5(db_path)
        while not await self._check_hash(db_hash):
            logging.info("DBS not matched!")
            self.pulled_db = True
            message = md_pb2.InitConn(action_type=InitConnActions.GET_DB)
            await self.send_protobuf(message)

            message = md_pb2.InitConn()
            message.ParseFromString(await self.reader.read())
            if not message.action_type == InitConnActions.GET_DB:
                raise UnexpectedAction()

            with open(db_path, 'wb') as f:
                f.write(message.db_file)
            db_hash = get_db_md5(db_path)

    async def send_protobuf(self, protobuf):
        if isinstance(protobuf, (str, bytes)):
            # protobuf was already serialized
            await self.writer.write(protobuf)
        await self.writer.write(protobuf.SerializeToString())

    async def __get_init_conn_result(self):
        message = md_pb2.DBResult()
        data = await self.reader.read()
        message.ParseFromString(data)
        if message.result != Results.SUCCESS:
            raise RESULTS_TO_EXCEPTIONS[message.result]
