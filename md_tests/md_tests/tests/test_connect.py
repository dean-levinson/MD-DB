from mdlib.exceptions import ClientIDDoesNotExist, ClientNotAllowed
from md_tests import *
from mdlib.db_utils import get_db_md5


@pytest_asyncio.fixture
async def mddb_unpermitted_client():
    client = Client((TEST_HOSTNAME, TESTS_PORT), client_id=TEST_UNPERMITTED_CLIENT_CREDS.id,
                    password=TEST_UNPERMITTED_CLIENT_CREDS.password, db_name=TEST_DB_NAME,
                    channel=asyncio.Queue(), db_directory=CLIENT_TEST_DIR)
    yield client


@pytest.mark.asyncio
async def test_simple_connect(mddb_client: Client):
    assert mddb_client._is_connected


@pytest.mark.asyncio
async def test_client_does_not_exist_failure():
    client = Client((TEST_HOSTNAME, TESTS_PORT), client_id=TEST_DOESNT_EXIST_CLIENT_CREDS.id,
                    password=TEST_DOESNT_EXIST_CLIENT_CREDS.password,
                    db_name=TEST_DB_NAME, channel=asyncio.Queue(), db_directory=CLIENT_TEST_DIR)
    with pytest.raises(ClientIDDoesNotExist):
        await client.connect(add_user=False)
    assert not client._is_connected


@pytest.mark.asyncio
async def test_client_does_not_permitted_failure():
    client = Client((TEST_HOSTNAME, TESTS_PORT), client_id=TEST_UNPERMITTED_CLIENT_CREDS.id,
                    password=TEST_UNPERMITTED_CLIENT_CREDS.password, db_name="secret_db", channel=asyncio.Queue(),
                    db_directory=CLIENT_TEST_DIR)
    with pytest.raises(ClientNotAllowed):
        await client.connect(add_user=False)
    assert not client._is_connected


@pytest.mark.asyncio
async def test_pull_db():
    client = Client((TEST_HOSTNAME, TESTS_PORT), client_id=TEST_REGULAR_CLIENT_CREDS.id,
                    password=TEST_REGULAR_CLIENT_CREDS.password, db_name=TEST_HASH_DB_NAME, channel=asyncio.Queue(),
                    db_directory=CLIENT_TEST_DIR)

    with SERVER_HASH_DB_RESOURCE:
        server_db_hash = get_db_md5(SERVER_HASH_DB_RESOURCE.resource_path)

    await client.connect()

    client_db_hash = get_db_md5(os.path.join(client.db_directory, client.db_name))

    assert server_db_hash == client_db_hash, "Different hash for server and client!"
