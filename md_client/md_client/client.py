import os
from mdlib.socket_utils import LengthReader, LengthWriter
from mdlib.db_utils import MDActions, get_db_md5
from mdlib.exceptions import *
from mdlib import md_pb2
from mdlib.md_pb2 import InitConnActions

import asyncio
import logging
from typing import Optional


class Client(object):
    def __init__(self, addr, db_name, client_id, channel: asyncio.Queue=None, db_directory=None):
        self.reader: Optional[LengthReader] = None
        self.writer: Optional[LengthWriter] = None
        self.hostname, self.port = addr
        self.db_name = db_name
        self.client_id = client_id
        self.db_directory = db_directory or '.'
        self.channel: asyncio.Queue = channel
        self.db_actions = MDActions(db_directory, db_name, self.channel, is_client=True)
        self.sync_task = None
        self._is_connected = False
        self.pulled_db = False

    async def connect(self, add_user=False, add_db_permissions=False):
        if self._is_connected:
            raise AlreadyConnected()

        reader, writer = await asyncio.open_connection(
            self.hostname, self.port)
        self.reader = LengthReader(reader)
        self.writer = LengthWriter(writer)

        await self._init_conn(add_user, add_db_permissions)

        self._is_connected = True

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
            logging.exception(e)

    async def _init_conn(self, add_user=False, add_db_permissions=False):
        if add_user:
            await self._add_user()
        if add_db_permissions:
            await self._add_db_permissions()

        await self._send_db_info()
        await self.pull_db()

    async def _send_db_info(self):
        message = md_pb2.InitConn(action_type=InitConnActions.DB_INFO, client_id=self.client_id, db_name=self.db_name)
        await self.send_protobuf(message)

    async def _add_user(self):
        message = md_pb2.InitConn(action_type=InitConnActions.ADD_USER, client_id=self.client_id)
        await self.send_protobuf(message)

    async def _add_db_permissions(self):
        message = md_pb2.InitConn(action_type=InitConnActions.ADD_PERMISSIONS, client_id=self.client_id, db_name=self.db_name)
        await self.send_protobuf(message)

    async def _check_hash(self, db_hash):
        message = md_pb2.InitConn(action_type=InitConnActions.CHECK_DB_HASH, db_hash=db_hash)
        await self.send_protobuf(message)
        message = md_pb2.InitConn(action_type=InitConnActions.GET_DB_STATE)
        await self.send_protobuf(message)

        message = md_pb2.InitConn()
        data = await self.reader.read()
        message.ParseFromString(data)
        if not message.action_type == InitConnActions.GET_DB_STATE:
            logging.info(f"mwssage: {data}")
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
