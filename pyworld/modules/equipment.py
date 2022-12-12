from enum import Enum
from typing import ClassVar, Dict, List, Optional, Tuple, Type

from pyworld.entity import CheckableProtocol, Entity
from pyworld.world import World


class EquipmentStatus(Enum):
    INIT = "Equipment initiating."
    NOT_CHECK = "A requirement check is needed."
    FAIL = "Some check not pass. Equipment may not work."
    FINE = "Equipment running fine."
    UPDATING = "Equipment info updating."


class CheckStatus(Enum):
    UNKNOWN = "Module doesn't have check method."
    PASSED = "Passed."
    FAILED = "Failed"


class Equipment():
    required_module: ClassVar[List[Type[Entity]]] = []

    def __init__(self) -> None:
        super().__init__()
        self.status: EquipmentStatus = EquipmentStatus.INIT
        self.belong: Optional[Entity] = None
        self.check_detail: Dict[str, CheckStatus] = {}

    def check_availability(
        self, belong: Entity
    ) -> Tuple[EquipmentStatus, Dict[str, CheckStatus]]:

        status: EquipmentStatus = EquipmentStatus.FINE
        check_detail: Dict[str, CheckStatus] = {}

        for module in self.required_module:
            if issubclass(module, CheckableProtocol):
                result: bool = module.check(belong)
                if result:
                    check_detail[module.__name__] = CheckStatus.PASSED
                else:
                    status = EquipmentStatus.FAIL
                    check_detail[module.__name__] = CheckStatus.FAILED
            else:
                status = EquipmentStatus.FAIL
                check_detail[module.__name__] = CheckStatus.UNKNOWN
        self.status = status
        self.check_detail = check_detail
        return self.status, self.check_detail

    def _tick(self, belong: Entity, world: World) -> None:
        self.check_availability(belong=belong)


class EquipmentMixin(Entity):
    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.equip_list = []

    def _equip_tick(self, belong: World):
        for equip in self.equip_list:
            equip._tick()

    pass
