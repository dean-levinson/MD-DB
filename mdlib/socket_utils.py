import struct
import asyncio
import logging


class LengthReader(asyncio.StreamReader):
    def __init__(self, reader: asyncio.StreamReader):
        self.reader = reader

    async def read(self):
        logging.debug("IN READ")
        size = await self.reader.read(4)
        total_size = struct.unpack('>I', size)[0]
        if total_size > 0:
            return await self.reader.read(total_size)
        return b''


class LengthWriter(asyncio.StreamWriter):
    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer

    async def write(self, data):
        total_size = len(data)
        size = struct.pack('>I', total_size)
        self.writer.write(size)
        if total_size > 0:
            self.writer.write(data)
        await self.writer.drain()
