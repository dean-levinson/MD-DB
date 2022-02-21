import sys
import click
import asyncio
import logging

from md_server.server import Server, AddAdminUserParams

logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")


async def run(host: str, port: int, add_admin_params: AddAdminUserParams, dbdir: str):
    """
    The main function that creates the Server object, it's sockets and servers as long as the server is running.
    @param str host: The host the server is listening on. If None the server will be listening on all interfaces.
    @param int port: The port the server will be listening on. Should be not in use on the host.
    @param AddAdminUserParams add_admin_params: Includes params that are used to add a new admin to the server.
    @param str dbdir: The directory in which the server will keep all it's dbs.
    """
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    s = Server(dbdir, add_admin_params)
    server = await asyncio.start_server(
        s.handle_conn, host, port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()


@click.command()
@click.option("--host", "-h", type=str, required=False, default=None)
@click.option("--port", "-p", type=int, required=True)
@click.option("--add-admin-user", type=bool, required=False, default=False, is_flag=True)
@click.option("--admin-client-id", type=int, required=False)
@click.option("--admin-password", type=str, required=False)
@click.option("--dbdir", type=str, required=False, default=".")
def main(host, port, add_admin_user, admin_client_id, admin_password, dbdir):
    if add_admin_user:
        assert admin_client_id and admin_password, "--admin-client-id and --admin-password should be passed when --add-admin-user"

    add_admin_params = AddAdminUserParams(add_admin_user, admin_client_id, admin_password)
    asyncio.run(run(host, port, add_admin_params, dbdir), debug=True)
