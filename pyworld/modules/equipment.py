from enum import Enum
from threading import Lock
from typing import Generic, List, Optional, Type, TypeVar, cast

from pyworld.control import ControlMixin
from pyworld.entity import Entity, with_instance_lock
from pyworld.world import World


class EquipStatus(Enum):
    INIT = "Equipment initiating."
    NOT_CHECK = "Still not checking."
    CHECK_FAIL = "Some check not pass. Equipment may not work."
    CHECK_PASS = "Equipment running fine."
    WORKING = "Equipment works fine."
    ERROR = "Equipment works into wrong."
    UPDATING = "Equipment info updating."


Requirement = TypeVar("Requirement")


class Equipment(Generic[Requirement], ControlMixin, Entity):
    require_module: Optional[Type[Requirement]] = None
    limit_num: int = 1

    def __init__(self) -> None:
        self.status: EquipStatus = EquipStatus.INIT
        super().__init__()
        self.belong: Optional[Entity] = None
        self.status = EquipStatus.NOT_CHECK

    def _on_equip(self, belong: Entity) -> None:
        if self._check_require(belong):
            self.status = EquipStatus.CHECK_PASS
        else:
            self.status = EquipStatus.CHECK_FAIL
        self.belong = belong

    def _on_unequip(self) -> None:
        self.status = EquipStatus.NOT_CHECK
        self.belong = None

    def _check_require(self, belong: Entity) -> bool:
        """
        Check input entity is satisfy for
        self.require_module
        """
        if self.require_module is None:
            return True

        return isinstance(belong, self.require_module)

    def _tick(self, o: Entity, w: World) -> None:
        super()._tick(o)


Equipments = TypeVar(name="Equipments", bound=Equipment)


class EquipmentMixin(Entity):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.equip_list: List[Equipment] = []

    def __static_init__(self) -> None:
        self.__equip_list_lock = Lock()
        return super().__static_init__()

    def __get_stack(
        self, equip: str | Equipments | Type[Equipments]
    ) -> List[Equipments]:
        """
        Return the list of equips in self.equip_list
        with given name/instance/type.
        """

        if isinstance(equip, str):
            name = equip
        elif isinstance(equip, Equipment):
            name = equip.__class__.__name__
        elif issubclass(equip, Equipment):
            name = equip.__name__

        rtn = []
        for i in self.equip_list:
            if i.__class__.__name__ == name:
                rtn.append(i)
        return rtn

    def __get_num(self, equip: str | Equipment | Type[Equipment]) -> int:
        """Return the number of equips in list with given name/instance/type."""
        return len(self.__get_stack(equip))

    def __equip_available_num(self, equip: Equipment | Type[Equipment]) -> int:
        """Return the number of equips that this Entity could add."""
        count = self.__get_num(equip)
        return equip.limit_num - count

    def __equip_check_limit(self, equip: Equipment | Type[Equipment]) -> bool:
        """Check whether self statisfy the input equip's num_limit."""
        available = self.__equip_available_num(equip)
        return available > 0

    def __equip_check_unique(self, equip: Equipment) -> bool:
        """Check whether self.equip_list already the same equip."""
        stack = self.__get_stack(equip)
        if stack == []:
            return True
        for each in stack:
            if each == equip:
                return False
        return True

    @with_instance_lock("_EquipmentMixin__equip_list_lock")
    def _equip_available(self, equip: Equipment | Type[Equipment]) -> int:
        return self.__equip_available_num(equip)

    @with_instance_lock("_EquipmentMixin__equip_list_lock")
    def _equip_add(self, equip: Equipment) -> bool:
        """
        Add new equip to self

        Respect to limit_num defined in Equipment subclass
        """

        if equip.belong is not None:
            return False

        if not self.__equip_check_limit(equip):
            return False

        if not equip._check_require(self):
            return False

        if not self.__equip_check_unique(equip):
            return False

        self.equip_list.append(equip)
        equip._on_equip(self)
        return True

    @with_instance_lock("_EquipmentMixin__equip_list_lock")
    def _equip_pop(
        self, target: str | Equipment | Type[Equipment], index: int = 0
    ) -> Optional[Equipment]:
        """
        Pop the equipment obj.

        name is the index for self.equip_dict
        index is for values in self.equip_dict, default is 0
        """
        stack: List[Equipment] = self.__get_stack(target)
        if len(stack) == 0:
            return None

        target_id = stack[index].uuid
        for i in range(len(self.equip_list)):
            if self.equip_list[i].uuid == target_id:
                rtn = self.equip_list.pop(i)
                rtn._on_unequip()
                return cast(Equipments, rtn)

    @with_instance_lock("_EquipmentMixin__equip_list_lock")
    def _equip_get(
        self, target: str | Type[Equipment], index: int = 0
    ) -> Optional[Equipment]:
        stack = self.__get_stack(target)
        if len(stack) == 0:
            return None
        return stack[index]

    def _equip_tick(self, belong: World) -> None:
        for each in self.equip_list:

            if not each._check_require(self):
                continue

            each._tick(o=self, w=belong)
