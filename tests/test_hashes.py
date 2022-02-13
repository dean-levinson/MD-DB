import os
import contextlib
import pytest
import json
from mdlib import md_pb2

from md_client.client import Client

TEST_DB_NAME = "test_db"
TEST_DIR = os.path.abspath('tests/')
TEST_HOSTNAME = ("127.0.0.1", 3938)

@contextlib.contextmanager
def mddb_client():
    try:
        c = Client(TEST_HOSTNAME, TEST_DB_NAME, 12345, TEST_DIR)
        yield c
    finally:
        pass


@pytest.mark.asyncio
async def test_equal_hashes(mddb_server):
    with mddb_client() as c:
        await c.connect()
        assert c._is_connected
        assert c.last_db_state == md_pb2.DBState.SYNCED


@pytest.mark.asyncio
async def test_not_equal_hashes(mddb_server):
    with mddb_client() as c:
        c.db_directory = '/tmp/'
        with open('/tmp/test_db', 'w') as f:
            json.dump({'bla': 1}, f)

        await c.connect()
        assert c._is_connected
        assert c.last_db_state == md_pb2.DBState.NOT_SYNCED
