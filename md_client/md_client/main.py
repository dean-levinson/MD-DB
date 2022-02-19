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


def db_backend(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

    tasks = asyncio.tasks.all_tasks(loop)
    for t in [t for t in tasks if (t.done() or t.cancelled())]:
        loop.run_until_complete(t)


def kill_event_loop(thread, loop):
    for task in asyncio.tasks.all_tasks(loop):
        task.cancel()

    loop.call_soon_threadsafe(loop.stop)
    thread.join()
    loop.close()

@click.command()
@click.option("--client-id", "-c", type=int, required=True, default=".")
@click.option("--host", "-h", type=str, required=True)
@click.option("--port", "-p", type=int, required=True)
@click.option("--dbname", "-d", type=str, required=True)
@click.option("--dbdir", type=str, required=False, default=".")
@click.option("--add-user", type=bool, required=False, is_flag=True, default=False)
@click.option("--add-permissions", type=bool, required=False, is_flag=True, default=False)
def main(client_id, host, port, dbname, dbdir, add_user, add_permissions):
    # Fixes Windows errors while running from cmd
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Create the actual db event loop and pass it to the thread
    loop = asyncio.new_event_loop()
    channel = asyncio.Queue()
    client_id = client_id
    client = Client((host, port), dbname, client_id, channel, db_directory=dbdir)

    thread = threading.Thread(target=db_backend, args=(loop,))
    thread.start()

    # handler = asyncio.run_coroutine_threadsafe(run(client, add_user, add_permissions), loop)
    
    connect_handler = asyncio.run_coroutine_threadsafe(client.connect(add_user, add_permissions), loop)
    
    try:
        # Wait up to 5 seconds to the server to connect
        connection_result = connect_handler.result(5)
    except Exception as e:
        kill_event_loop(thread, loop)
        error = termcolor.colored(f"{e.__class__.__name__}", "red", attrs=["bold"])
        logging.error(f"Error while trying to connect to server: {error}")
        return

    client_handler = asyncio.run_coroutine_threadsafe(client.sync_with_remote(), loop)

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

    kill_event_loop(thread, loop)
