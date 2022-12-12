from enum import Enum
from typing import Generic, Optional, Type, TypeVar

from pyworld.entity import Entity
from pyworld.world import World


class EquipmentMixin(Entity):
    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.equip_list = []

    def _equip_tick(self, belong: World):
        for equip in self.equip_list:
            equip._tick()

    pass


class EquipStatus(Enum):
    INIT = "Equipment initiating."
    NOT_CHECK = "A requirement check is needed."
    FAIL = "Some check not pass. Equipment may not work."
    FINE = "Equipment running fine."
    UPDATING = "Equipment info updating."


class CheckStatus(Enum):
    UNKNOWN = "Module doesn't have check method."
    PASSED = "Passed."
    FAILED = "Failed"


Requirement = TypeVar("Requirement")


class Equipment(Generic[Requirement]):
    require_module: Type[Requirement]

    def __init__(self) -> None:
        super().__init__()
        self.status: EquipStatus = EquipStatus.INIT
        self.belong: Optional[Entity] = None

    def check_availability(self) -> bool:

        _flag: bool = True
        if isinstance(self.belong, self.require_module):
            self.status = EquipStatus.FINE
        else:
            self.status = EquipStatus.FAIL
            _flag = False

        return _flag

    def _tick(self, o: Requirement, w: World) -> None:
        self.check_availability()
