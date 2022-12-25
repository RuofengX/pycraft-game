from enum import IntFlag, Enum, auto


class CallStatus(IntFlag):
    # DO NOT CHANGE THE ORDER
    INIT = auto()  # 1, 0b001, whether is init
    _DONE = auto()  # 2, 0b010, whether process is finished
    _WITH_ERROR = auto()  # 4, 0b100, whether has ERROR info
    SUCCESS = INIT | _DONE  # 3, 0b011
    FAIL = INIT | _WITH_ERROR  # 5, 0b101
    WARNING = SUCCESS | _WITH_ERROR  # 7, 0b111, SUCCESS but with errors

    def __repr__(self) -> str:
        return str(self.name)


class EquipStatus(Enum):
    OK = 1  # "Equiped by an owner. Require satisfied. Ready to work."
    CHECK_FAIL = 2  # "Some check not pass. Equipment may not work."
    NO_BELONG = 3  # "Equip do not have Owner"

    def __repr__(self) -> str:
        return str(self.name)
