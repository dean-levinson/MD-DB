import asyncio
import logging

from md_server.server import Server

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s]: %(message)s")


async def main():
    s = Server()
    server = await asyncio.start_server(
        s.handle_conn, '127.0.0.1', 8888)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main(), debug=True)

