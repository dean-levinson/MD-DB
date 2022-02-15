import functools
import sys
import asyncio
import logging
import threading
import IPython
from unittest import async_case

from md_client.client import Client
from md_client.client_actions import ClientActions

logging.basicConfig(level=logging.ERROR, format="[%(levelname)s]: %(message)s")

async def run(c: Client):
    await c.connect(add_user=False, add_db_permissions=True)
    await c.sync_task


def db_backend(loop: asyncio.AbstractEventLoop, client: Client):
    # Fixes Windows errors while running from cmd
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.set_event_loop(loop)
    loop.call_soon(lambda: asyncio.create_task(run(client)))
    loop.run_forever()


def main():
    hostname = "127.0.0.1"
    db_name ="mydb"
    db_directory = "."
    client_id = 4313

    # Create the actual db event loop and pass i to the thread
    loop = asyncio.new_event_loop()
    client = Client((hostname, 8888), db_name, client_id, db_directory)
    thread = threading.Thread(target=db_backend, args=(loop, client))
    thread.start()

    IPython.start_ipython(user_ns={'client': ClientActions(loop, client, "mydb", ".")})
    
