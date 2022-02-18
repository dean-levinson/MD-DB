import click
import sys
import asyncio
import logging
import threading
from concurrent import futures
import IPython
import termcolor

from md_client.client import Client
from md_client.client_actions import ClientActions
from traitlets.config.loader import Config

logging.basicConfig(level=logging.ERROR, format="[%(levelname)s]: %(message)s")


async def run(c: Client):
    try:
        await c.connect(add_user=False, add_db_permissions=True)
        await c.sync_with_remote()
    except asyncio.CancelledError:
        await c.disconnect()


def db_backend(loop: asyncio.AbstractEventLoop, client: Client):
    asyncio.set_event_loop(loop)
    loop.run_forever()

    tasks = asyncio.tasks.all_tasks(loop)
    for t in [t for t in tasks if (t.done() or t.cancelled())]:
        loop.run_until_complete(t)


def kill_event_loop(loop):
    loop.call_soon_threadsafe(loop.stop)
    for task in asyncio.tasks.all_tasks(loop):
        task.cancel()


@click.command()
@click.option("--client-id", "-c", type=int, required=True, default=".")
@click.option("--host", "-h", type=str, required=True)
@click.option("--port", "-p", type=int, required=True)
@click.option("--dbname", "-d", type=str, required=True)
@click.option("--dbdir", type=str, required=False, default=".")
def main(client_id, host, port, dbname, dbdir):
    # Fixes Windows errors while running from cmd
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Create the actual db event loop and pass it to the thread
    loop = asyncio.new_event_loop()
    channel = asyncio.Queue()
    client_id = client_id
    client = Client((host, port), dbname, client_id, channel, db_directory=dbdir)

    thread = threading.Thread(target=db_backend, args=(loop, client))
    thread.start()

    handler = asyncio.run_coroutine_threadsafe(run(client), loop)

    # In case connect didn't work for 0.125 seconds, kill event_loop
    try:
        print(handler.exception(0.125))
        kill_event_loop(loop)
        return
    except futures.TimeoutError:
        pass

    banner = termcolor.colored("\nWelcome to MD-DB!", "green", attrs=["bold"])
    banner2 = termcolor.colored("Use client.* functions\n", "white", attrs=["bold"])
    config = Config()
    config.TerminalInteractiveShell.banner1 = banner
    config.TerminalInteractiveShell.banner2 = banner2

    IPython.start_ipython(
        user_ns={
            'client': ClientActions(loop, client, channel, dbname, dbdir)
        },
        argv=[],
        config=config
    )

    kill_event_loop(loop)
