from md_tests import *

from mdlib.db_utils import DBMessage, serialize_db_value, get_db_value
from mdlib.md_pb2 import MessageTypes, Results, ValueType

@pytest.mark.asyncio
async def test_message_serialization():
    """
    Test message serialization ond parsing mechanism
    """
    message = DBMessage()
    message.message_type = MessageTypes.DB_RESULT
    message.db_result.result = Results.SUCCESS
    message.db_value.value_type = ValueType.STR
    message.db_value.value = b"test_value"

    protobuf = message.SerializeToString()

    new_message = DBMessage()
    new_message.ParseFromString(protobuf)

    assert message.message_type == new_message.message_type
    assert message.db_result.result == new_message.db_result.result
    assert message.db_value.value_type == new_message.db_value.value_type
    assert message.db_value.value == new_message.db_value.value

@pytest.mark.asyncio
async def test_value_serialization():
    """
    Test value serialization ond parsing mechanism
    """
    value = {1: 2, 3: 4}
    message = DBMessage()
    message.message_type = MessageTypes.DB_RESULT
    message.db_result.result = Results.SUCCESS
    value_type, value_bytes = serialize_db_value(value)
    message.db_value.value_type = value_type
    message.db_value.value = value_bytes

    assert value == get_db_value(message.SerializeToString())
