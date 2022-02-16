import asyncio
import functools
from mdlib.db_utils import MDActions
from mdlib.md_pb2 import DBAction, Actions

from md_client.client import Client

class ClientActions(object):
    def __init__(self, loop, client: Client, db_name, db_directory):
        self.loop: asyncio.AbstractEventLoop = loop
        self.client = client

    def add_item(self, key, value):
        """
        Add item to the DB
        """
        func = functools.partial(self.__add_item_inner, key, value)
        asyncio.run_coroutine_threadsafe(func(), self.loop)

    def delete_item(self, key):
        """
        Delete item from the DB
        """
        func = functools.partial(self.__delete_item_inner, key)
        asyncio.run_coroutine_threadsafe(func(), self.loop)

    def get_all_keys(self):
        handler = asyncio.run_coroutine_threadsafe(self.__get_all_keys_inner(), self.loop)
        return handler.result(1)

    async def __add_item_inner(self, key, value):
        data = self.client.db_actions.add_item(key, value)
        await self.client.writer.write(data)

    async def __get_all_keys_inner(self):
        data = self.client.db_actions.get_all_keys()
        await self.client.writer.write(data)
        return "kaka"

    async def __delete_item_inner(self, key):
        data = self.client.db_actions.delete_key(key)
        await self.client.writer.write(data)
