class MDActions(object):
    """
    for md_client - After receive protobuf from md_server, change the db accordingly.
    for md_server - Change the local db.
    """

    def __init__(self, db_directory, db_name):
        pass

    def handle_protobuf(self, protobuf_obj):
        # call DBProtocol to parse obj
        # call switch case
        pass

    def add_key(self):
        pass

    def set_key(self):
        pass

    def delete_key(self):
        pass


class MDProtocol(object):
    KEYS = {
        "add": 1,
        "delete": 2
    }

    def __init__(self):
        pass

    def create_message(self, action, key, value=None):
        # protobuf.pasten()
        pass
