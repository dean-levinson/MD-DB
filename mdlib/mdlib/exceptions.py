class AlreadyConnected(Exception):
    pass


class InvalidAction(Exception):
    pass


class UnexpectedAction(Exception):
    pass


class KeyAlreadyExists(Exception):
    pass


class KeyDoesNotExists(Exception):
    pass


class ClientIDAlreadyExists(Exception):
    pass


class ClientIDDoesNotExist(Exception):
    pass


class ClientNotAllowed(Exception):
    pass

class IncorrectPassword(Exception):
    pass
