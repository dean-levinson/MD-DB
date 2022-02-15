import asyncio
import functools
from mdlib.db_utils import MDActions
from mdlib.md_pb2 import DBAction, Actions

from md_client.client import Client

class ClientActions(object):
    def __init__(self, loop, client: Client, db_name, db_directory):
        self.loop: asyncio.AbstractEventLoop = loop
        self.client = client

    async def __add_item_inner(self, key, value):
        data = self.client.db_actions.add_item(key, value)
        await self.client.writer.write(data)

    def add_item(self, key, value):
        """
        Add item to the DB
        """
        func = functools.partial(self.__add_item_inner, key, value)
        print(asyncio.all_tasks(self.loop))
        asyncio.run_coroutine_threadsafe(func(), self.loop)
        print(asyncio.all_tasks(self.loop))