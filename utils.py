from enum import Enum


class ClientCommand(Enum):
    FULL = 'full'
    DIFF = 'diff'
    DONE = 'done'


if __name__ == "__main__":
    c = ClientCommand
    pass
