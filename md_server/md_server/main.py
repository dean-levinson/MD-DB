import click
import asyncio
import logging

from md_server.server import Server

logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")

async def run(host, port, dbdir):
    s = Server(dbdir)
    server = await asyncio.start_server(
        s.handle_conn, host, port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

@click.command()
@click.option("--host", "-h", type=str, required=True)
@click.option("--port", "-p", type=int, required=True)
@click.option("--dbdir", type=str, required=False, default=".")
def main(host, port, dbdir):
    asyncio.run(run(host, port, dbdir), debug=True)
