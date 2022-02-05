import asyncio
from mdlib.db_utils import MDActions, MDProtocol

class Client(object):
    def __init__(self, hostname, db_name, db_directory=None):
        self.reader = None # type: asyncio.StreamReader
        self.writer = None # type: asyncio.StreamWriter
        self.db_directory = db_directory
        self.db_actions = MDActions(db_directory, db_name)

        self.connect(hostname, db_name)
        self.pull_db()
        self.sync_task = asyncio.create_task(self.sync_with_remote())

    async def sync_with_remote(self):
        while True:
            action = await self.reader.read()
            self.db_actions.handle_protobuf(action)

    def pull_db(self):
        pass

    def connect(self, hostname, db_name):
        self.reader, self.writer = await asyncio.open_connection(
            hostname, 8888)

        # send protobuf of self.client_id, self.db_name

    def send_protobuf(self, protobuf):
        self.logger.debug(f"Sent protobuf {protobuf}")
        self.writer.write(protobuf)


    def add_item(self, item):
        # message = self.md_protocol.create_message(ADD, paten)
        # self.send_protobuf(message)

    def delete_item(self, item):
        pass


async def main():
    # c = Client(hostname, db_name, db_directory)

if __name__ == "__main__":
    asyncio.run(main())
