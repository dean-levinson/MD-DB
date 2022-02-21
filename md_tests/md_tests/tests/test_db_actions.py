from mdlib.exceptions import KeyDoesNotExists
from md_tests import *


@pytest.mark.asyncio
async def test_get_all_keys(mddb_client: Client):
    keys = await run_client_action(mddb_client, "get_all_keys", should_read_result=True)
    assert isinstance(keys, list)


@pytest.mark.asyncio
async def test_set_value(mddb_client: Client):
    await run_client_action(mddb_client, "set_value", "21", 12)
    db_result = await run_client_action(mddb_client, "get_key_value", "21", should_read_result=True)

    assert db_result == 12


@pytest.mark.asyncio
@pytest.mark.parametrize("item", [("21", 12), ("17", 3)])
async def test_get_key_value(mddb_client: Client, item):
    key, target_value = item
    current_value = await run_client_action(mddb_client, "get_key_value", key, should_read_result=True)
    assert current_value == target_value


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [1, "2", {3: 4}, [5, 6]])
async def test_add_item(mddb_client: Client, value):
    key = "17"
    await run_client_action(mddb_client, "add_item", key, value)
    db_result = await run_client_action(mddb_client, "get_key_value", key, should_read_result=True)
    assert db_result == value


# @pytest.mark.asyncio
# async def test_delete_key(mddb_client: Client):
#     key = "21"
#     await run_client_action(mddb_client, "delete_key", key, should_read_result=True)
#     # await run_client_action(mddb_client, "get_key_value", "17", should_read_result=True)
#     with pytest.raises(KeyDoesNotExists):
#         db_result = await run_client_action(mddb_client, "get_key_value", key, should_read_result=True)
