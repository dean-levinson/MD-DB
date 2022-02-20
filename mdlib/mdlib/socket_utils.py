import struct
import asyncio


class LengthReader(asyncio.StreamReader):
    def __init__(self, reader: asyncio.StreamReader):
        self.reader = reader

    async def read(self):
        """
        Reads the 4 bytes which encode the message's size,
        then reads the rest of the message using the size it got.
        """
        size = await self.reader.read(4)
        total_size = struct.unpack('>I', size)[0]
        if total_size > 0:
            return await self.reader.read(total_size)
        return b''


class LengthWriter(asyncio.StreamWriter):
    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer

    async def write(self, data):
        """
        Send the message and 4 bytes representing the length of the message.
        """
        buf = struct.pack('>I', len(data))
        if len(data) > 0:
            buf += data

        self.writer.write(buf)
        await self.writer.drain()
