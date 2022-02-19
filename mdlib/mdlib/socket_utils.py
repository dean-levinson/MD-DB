import struct
import asyncio


class LengthReader(asyncio.StreamReader):
    def __init__(self, reader: asyncio.StreamReader):
        self.reader = reader

    async def read(self):
        size = await self.reader.read(4)
        total_size = struct.unpack('>I', size)[0]
        if total_size > 0:
            return await self.reader.read(total_size)
        return b''


class LengthWriter(asyncio.StreamWriter):
    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer

    async def write(self, data):
        buf = struct.pack('>I', len(data))
        if len(data) > 0:
            buf += data

        self.writer.write(buf)
        await self.writer.drain()
