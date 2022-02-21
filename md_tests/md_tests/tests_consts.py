from md_tests.test_utils import *

TEST_DB_NAME = "test_db"
TEST_HASH_DB_NAME = "test_hash_db"
TEST_DB_USERS_NAME = "users"
TESTS_PORT = 5555
TEST_HOSTNAME = "127.0.0.1"
TEST_COMMANDS_TIMEOUT = 5

SERVER_TEST_DIR = os.path.join(TEST_DIR, "server")
CLIENT_TEST_DIR = os.path.join(TEST_DIR, "client")

TEST_ADMIN_CLIENT_CREDS = ClientCreds(1234, "123")
TEST_REGULAR_CLIENT_CREDS = ClientCreds(4321, "password")
TEST_UNPERMITTED_CLIENT_CREDS = ClientCreds(321, "umpermitted")
TEST_DOESNT_EXIST_CLIENT_CREDS = ClientCreds(576, "not_exist")
TEST_CLIENT_WITHOUT_PERMISSION_YET_CREDS = ClientCreds(5432, "going_to_be_permitted")

SERVER_DB_RESOURCE = TestResource(TEST_DB_NAME, "server")
SERVER_DB_USERS_RESOURCE = TestResource(TEST_DB_USERS_NAME, "server")
SERVER_HASH_DB_RESOURCE = TestResource(TEST_HASH_DB_NAME, "server")
