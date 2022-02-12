import sys
import asyncio
import logging

from md_client.client import Client

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s]: %(message)s")


async def main():
    hostname = "127.0.0.1"
    db_name ="mydb"
    db_directory = "."
    client_id = 4313
    c = Client(hostname, db_name, client_id, db_directory)
    await c.connect(add_user=False, add_db_permissions=True)
    await c.sync_task

if __name__ == "__main__":
    # Fixes Windows errors while running from cmd
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(), debug=True)
