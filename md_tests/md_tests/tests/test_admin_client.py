from md_tests import *


@pytest_asyncio.fixture
async def admin_client():
    client_creds = TEST_ADMIN_CLIENT_CREDS
    client = Client((TEST_HOSTNAME, TESTS_PORT), client_id=client_creds.id, password=client_creds.password,
                    db_name=TEST_DB_USERS_NAME, channel=asyncio.Queue(), db_directory=CLIENT_TEST_DIR)

    await client.connect()

    return client


@pytest.mark.asyncio
async def test_add_permissions(admin_client):
    client_creds = TEST_CLIENT_WITHOUT_PERMISSION_YET_CREDS

    client_info = await run_client_action(admin_client, "get_key_value", str(client_creds.id), should_read_result=True)
    client_info["allowed_dbs"].append(TEST_DB_NAME)

    await run_client_action(admin_client, "set_value", str(client_creds.id), client_info)

    updated_client_info = await run_client_action(admin_client, "get_key_value", str(client_creds.id),
                                                  should_read_result=True)

    assert TEST_DB_NAME in updated_client_info["allowed_dbs"]

    # Try to connect to DB
    client = Client((TEST_HOSTNAME, TESTS_PORT), client_id=client_creds.id, password=client_creds.password,
                    db_name=TEST_DB_NAME, channel=asyncio.Queue(), db_directory=CLIENT_TEST_DIR)

    await client.connect()
    assert client._is_connected
