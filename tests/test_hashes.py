import os
import pytest
import json

TEST_DB_NAME = "test_db"
TEST_DIR = os.path.abspath('tests/')
TEST_HOSTNAME = ("127.0.0.1", 3938)

@pytest.mark.asyncio
async def test_equal_hashes(mddb_server, mddb_client):
    await mddb_client.connect(add_db_permissions=True)
    assert mddb_client._is_connected
    assert not mddb_client.pulled_db


@pytest.mark.asyncio
async def test_not_equal_hashes(mddb_server, mddb_client):
    mddb_client.db_directory = '/tmp/'
    with open('/tmp/test_db', 'w') as f:
        json.dump({'bla': 1}, f)

    await mddb_client.connect(add_db_permissions=True)
    assert mddb_client._is_connected
    assert mddb_client.pulled_db
