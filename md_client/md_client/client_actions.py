import ast
import asyncio
import logging
import concurrent.futures
from mdlib.md_pb2 import Actions, DBResult, Results

from md_client.client import Client
from mdlib.db_utils import RESULTS_TO_EXCEPTIONS


class ClientActions(object):
    """
    All the functions here are duplicated... In order to change this we need to implement code in runtime...
    """

    def __init__(self, loop, client: Client, channel: asyncio.Queue, db_name, db_directory):
        self.__loop: asyncio.AbstractEventLoop = loop
        self.__client = client
        self.__channel: asyncio.Queue = channel

    def __handle_coroutine(self, task_coroutine, channel_coroutine):
        try:
            db_result = channel_coroutine.result(5)
            if db_result.result != Results.SUCCESS:
                raise RESULTS_TO_EXCEPTIONS[db_result.result]

            return db_result

        except concurrent.futures.TimeoutError as e:
            logging.error('The coroutine took too long, cancelling the task...')
            channel_coroutine.cancel()
            task_coroutine.cancel()
            logging.error(f'The task coroutine raised an exception: {task_coroutine.exception()!r}')

    def add_item(self, key, value):
        """
        Add item to the DB
        """
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__add_item_inner(key, value), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))

    def delete_item(self, key):
        """
        Delete item from the DB
        """
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__delete_item_inner(key), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))

    def get_all_keys(self):
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__get_all_keys_inner(), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))
        return ast.literal_eval(db_result.result_value)

    def set_value(self, key, value):
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__set_value_inner(key, value), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))

    def get_key_value(self, key):
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__get_key_value_inner(key), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))
        return db_result.result_value

    def delete_key(self, key):
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__delete_key(key), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))

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
