import ast
import asyncio
import functools
from mdlib.md_pb2 import Actions, DBResult, Results

from md_client.client import Client
from mdlib.db_utils import RESULTS_TO_EXCEPTIONS

class ClientActions(object):
    """
    TODO: All the functions here are duplicated.. 
    need to implement dynamic functions with lambdas or something
    """
    def __init__(self, loop, client: Client, channel: asyncio.Queue, db_name, db_directory):
        self.__loop: asyncio.AbstractEventLoop = loop
        self.__client = client
        self.__channel: asyncio.Queue = channel

    def __handle_result(self, db_result):
        if db_result.result != Results.SUCCESS:
            raise RESULTS_TO_EXCEPTIONS[db_result.result]

    def add_item(self, key, value):
        """
        Add item to the DB
        """
        func = functools.partial(self.__add_item_inner, key, value)
        asyncio.run_coroutine_threadsafe(func(), self.__loop)
        db_result = asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop).result(5)
        self.__handle_result(db_result)

    def delete_item(self, key):
        """
        Delete item from the DB
        """
        func = functools.partial(self.__delete_item_inner, key)
        asyncio.run_coroutine_threadsafe(func(), self.__loop)
        db_result = asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop).result(5)
        self.__handle_result(db_result)

    def get_all_keys(self):
        handler = asyncio.run_coroutine_threadsafe(self.__get_all_keys_inner(), self.__loop)
        db_result = asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop).result(5)
        self.__handle_result(db_result)
        return ast.literal_eval(db_result.result_value)

    def set_value(self, key, value):
        handler = asyncio.run_coroutine_threadsafe(self.__set_value_inner(key, value), self.__loop)
        db_result = asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop).result(5)
        self.__handle_result(db_result)

    def get_key_value(self, key):
        handler = asyncio.run_coroutine_threadsafe(self.__get_key_value_inner(key), self.__loop)
        db_result = asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop).result(5)
        self.__handle_result(db_result)
        return db_result.result_value

    def delete_key(self, key):
        handler = asyncio.run_coroutine_threadsafe(self.__delete_key(key), self.__loop)
        db_result = asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop).result(5)
        self.__handle_result(db_result)

    async def __delete_key(self, key):
        data = self.__client.db_actions.delete_key(key)
        await self.__client.writer.write(data)

    async def __get_key_value_inner(self, key):
        data = self.__client.db_actions.get_key_value(key)
        await self.__client.writer.write(data)

    async def __set_value_inner(self, key, value):
        data = self.__client.db_actions.set_value(key, value)
        await self.__client.writer.write(data)

    async def __add_item_inner(self, key, value):
        data = self.__client.db_actions.add_item(key, value)
        await self.__client.writer.write(data)

    async def __get_all_keys_inner(self):
        data = self.__client.db_actions.get_all_keys()
        await self.__client.writer.write(data)

    async def __delete_item_inner(self, key):
        data = self.__client.db_actions.delete_key(key)
        await self.__client.writer.write(data)
