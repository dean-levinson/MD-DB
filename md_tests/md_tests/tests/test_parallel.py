from md_tests import *


@pytest.mark.asyncio
async def test_parallel_run():
    """
    test parallel run of 2 different clients with the same server.
    """
    client_1 = Client((TEST_HOSTNAME, TESTS_PORT), client_id=TEST_REGULAR_CLIENT_CREDS.id,
                      password=TEST_REGULAR_CLIENT_CREDS.password, db_name=TEST_DB_NAME, channel=asyncio.Queue(),
                      db_directory=CLIENT_TEST_DIR)

    client_2 = Client((TEST_HOSTNAME, TESTS_PORT), client_id=TEST_ADMIN_CLIENT_CREDS.id,
                      password=TEST_ADMIN_CLIENT_CREDS.password,
                      db_name=TEST_DB_NAME, channel=asyncio.Queue(), db_directory=CLIENT_TEST_DIR)

    await client_1.connect(add_user=False)
    await client_2.connect(add_user=False)

    new_key = "new_item"
    new_value = 14
    await run_client_action(client_1, "add_item", new_key, new_value)
    returned_value = await run_client_action(client_2, "get_key_value", new_key, should_read_result=True)

    assert new_value == returned_value, "sync failed..."
