import struct
import asyncio
import logging


class LengthReader(asyncio.StreamReader):
    def __init__(self, reader: asyncio.StreamReader):
        self.reader = reader

    async def read(self):
        size = await self.reader.read(4)
        total_size = struct.unpack('>I', size)[0]
        print(total_size)
        if total_size > 0:
            return await self.reader.read(total_size)
        return b''


class LengthWriter(asyncio.StreamWriter):
    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer

    def write(self, data):
        logging.debug(f"in write {data}")
        total_size = len(data)
        pack1 = struct.pack('>I', total_size)
        self.writer.write(pack1)
        if total_size > 0:
            self.writer.write(data)
