import os
import pytest
import pytest_asyncio
import asyncio

from md_server.server import Server
from md_client.client import Client
import logging

TEST_DB_NAME = "test_db"
TEST_DIR = os.path.abspath('tests/')
TESTS_PORT = 3938
TEST_HOSTNAME = "127.0.0.1"

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s]: %(message)s")

@pytest_asyncio.fixture
async def empty_db():
    open(os.path.join(TEST_DIR, TEST_DB_NAME), 'a').close()
    yield
    os.remove(os.path.join(TEST_DIR, TEST_DB_NAME))


@pytest_asyncio.fixture
def mddb_client():
    c = Client(TEST_HOSTNAME, TEST_DB_NAME, 12345, db_directory=TEST_DIR)
    yield c


@pytest_asyncio.fixture
async def mddb_server():
    s = Server(TEST_DIR)
    server = await asyncio.start_server(
        s.handle_conn, TEST_HOSTNAME, TESTS_PORT)

    async with server:
        yield server


""" @pytest.fixture
async def mddb_client():
    s = Client(TEST_HOSTNAME, TEST_DB_NAME, 12345, TEST_DIR)
    await s.connect()
 """

