import os
import shutil
import pytest
import pytest_asyncio
import asyncio
import logging

from md_tests.tests_consts import *
from md_tests.test_utils import *
from md_server.server import Server, AddAdminUserParams
from md_client.client import Client
from mdlib.db_utils import get_db_value

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s]: %(message)s")


async def run_client_action(mddb_client: Client, action: str, *args, **kwargs):
    db_value = None
    should_read_result = kwargs.get('should_read_result', False)

    protobuf_obj = getattr(mddb_client.db_actions, action)(*args, **kwargs)
    await asyncio.wait_for(mddb_client.writer.write(protobuf_obj), TEST_COMMANDS_TIMEOUT)

    if should_read_result:
        protobuf_result = await mddb_client.reader.read()
        db_value = get_db_value(protobuf_result)

    return db_value


@pytest.yield_fixture(scope='function')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session', autouse=True)
def setup_dbs():
    with DB_RESOURCE, DB_USERS_RESOURCE:
        yield


@pytest_asyncio.fixture
async def mddb_client():
    client = Client((TEST_HOSTNAME, TESTS_PORT), client_id=TEST_REGULAR_CLIENT_CREDS.id,
                    password=TEST_REGULAR_CLIENT_CREDS.password, db_name=TEST_DB_NAME,
                    channel=asyncio.Queue(), db_directory=CLIENT_TEST_DIR)

    await client.connect(add_user=False)

    yield client


@pytest_asyncio.fixture(scope="function", autouse=True)
async def mddb_server(request):
    s = Server(SERVER_TEST_DIR, add_admin_params=AddAdminUserParams(False, TEST_ADMIN_CLIENT_CREDS.id,
                                                                    TEST_ADMIN_CLIENT_CREDS.password))

    server = await asyncio.start_server(
        s.handle_conn, TEST_HOSTNAME, TESTS_PORT)

    async with server:
        yield server

    server.close()
