import asyncio
import logging
import concurrent.futures
from mdlib.md_pb2 import Actions, DBResult, Results
from mdlib.db_utils import serialize_db_value

from md_client.client import Client
from mdlib.db_utils import RESULTS_TO_EXCEPTIONS, get_db_value


class ClientActions(object):
    """
    All the functions here are duplicated, in order to change this we need to implement code in runtime...
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, client: Client, channel: asyncio.Queue):
        self.__loop: asyncio.AbstractEventLoop = loop
        self.__client = client
        self.__channel: asyncio.Queue = channel

    def __handle_coroutine(self, task_coroutine, channel_coroutine):
        """
        Waits for result from the channel, then raises exception accordingly if needed.
        If no valid answer return, cancels the channel's coroutine (which will probably never return),
        and the task_coroutine, which is no longer relevant.
        """
        try:
            db_result = channel_coroutine.result(5)
            if db_result.db_result.result != Results.SUCCESS:
                raise RESULTS_TO_EXCEPTIONS[db_result.db_result.result]
            return db_result

        except concurrent.futures.TimeoutError as e:
            logging.error('The coroutine took too long, cancelling the task...')
            channel_coroutine.cancel()
            task_coroutine.cancel()
            exc = task_coroutine.exception()
            logging.error(f'The task coroutine raised an exception: {exc}')
            raise exc

    def add_item(self, key, value):
        """
        Add a key-value item to the DB.
        @param str key: The key of the item. Must be a string.
        @param value: The value of the key. Can be any python serialized type.
        """
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__add_item_inner(key, value), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))

    def delete_item(self, key):
        """
        Delete item from the DB.
        @param str key: The key of the item that will be deleted.
        """
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__delete_item_inner(key), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))

    def get_all_keys(self):
        """
        Get a list of all the keys from the DB.
        """
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__get_all_keys_inner(), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))
        return get_db_value(db_result)

    def set_value(self, key, value):
        """
        Set a value to the key `key`, that already exists.
        @param str key: The key that will be edited. Must exist before running the function.
        @param value: The new value that would be set. Can be of any type.
        """
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__set_value_inner(key, value), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))

    def get_key_value(self, key):
        """
        Returns the value of key from the DB.
        @param str key: The key that it's value will be retrieved. Must exist before running the function.
        """
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__get_key_value_inner(key), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))
        return get_db_value(db_result)

    def delete_key(self, key):
        """
        Deletes the key and it's value.
        @param str key: The key of the item that will be deleted.
        """
        task_coroutine = asyncio.run_coroutine_threadsafe(self.__delete_key(key), self.__loop)
        db_result = self.__handle_coroutine(task_coroutine,
                                            asyncio.run_coroutine_threadsafe(self.__channel.get(), self.__loop))

    async def __delete_key(self, key):
        """
        inner function that gets the relevant protobuf from db_actions and sends it to the server.
        """
        data = self.__client.db_actions.delete_key(key)
        await self.__client.writer.write(data)

    async def __get_key_value_inner(self, key):
        """
        inner function that gets the relevant protobuf from db_actions and sends it to the server.
        """
        data = self.__client.db_actions.get_key_value(key)
        await self.__client.writer.write(data)

    async def __set_value_inner(self, key, value):
        """
        inner function that gets the relevant protobuf from db_actions and sends it to the server.
        """
        data = self.__client.db_actions.set_value(key, value)
        await self.__client.writer.write(data)

    async def __add_item_inner(self, key, value):
        """
        inner function that gets the relevant protobuf from db_actions and sends it to the server.
        """
        data = self.__client.db_actions.add_item(key, value)
        await self.__client.writer.write(data)

    async def __get_all_keys_inner(self):
        """
        inner function that gets the relevant protobuf from db_actions and sends it to the server.
        """
        data = self.__client.db_actions.get_all_keys()
        await self.__client.writer.write(data)

    async def __delete_item_inner(self, key):
        """
        inner function that gets the relevant protobuf from db_actions and sends it to the server.
        """
        data = self.__client.db_actions.delete_key(key)
        await self.__client.writer.write(data)
