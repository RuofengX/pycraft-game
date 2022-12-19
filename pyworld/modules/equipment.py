from enum import Enum
from typing import Generic, Optional, Protocol, Type, TypeVar, Dict, List
from pyworld.control import ControlMixin

from pyworld.entity import Checkable, Entity
from pyworld.world import World


class EquipStatus(Enum):
    INIT = "Equipment initiating."
    NOT_CHECK = "Still not checking."
    FAIL = "Some check not pass. Equipment may not work."
    FINE = "Equipment running fine."
    UPDATING = "Equipment info updating."


Requirement = TypeVar("Requirement", bound=Protocol)


class Equipment(Generic[Requirement], ControlMixin, Entity):
    require_module: Type[Requirement]
    limit_num: int = 1

    def __init__(self) -> None:
        self.status: EquipStatus = EquipStatus.INIT
        super().__init__()
        self.belong: Optional[Entity] = None
        self.status = EquipStatus.NOT_CHECK

    def check_require(self, ent: Entity) -> bool:
        """
        Check input entity is satisfy for
        self.require_module
        """

        return isinstance(ent, self.require_module)

    def _on_equip(self, belong: Entity) -> None:
        if self.check_require(ent=belong):
            self.status = EquipStatus.FINE
        else:
            self.status = EquipStatus.FAIL
        self.belong = belong

    def _on_unequip(self) -> None:
        self.status = EquipStatus.NOT_CHECK
        self.belong = None

    def _tick(self, o: Entity, w: World) -> None:
        super()._tick(belong=w)


class EquipmentMixin(Entity):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.equip_list: List[Equipment] = []
        self.equip_ensure_require: bool = True

    def __get_stack(self, equip: str | Equipment | Type[Equipment]) -> List[Equipment]:
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

    def _equip_available_num(self, equip: Equipment) -> int:
        """Return the number of equips that this Entity could add."""
        count = self.__get_num(equip)
        return equip.limit_num - count

    def _equip_check_limit(self, equip: Equipment) -> bool:
        """Check whether self statisfy the input equip's num_limit."""
        rtn = self._equip_available_num(equip)
        return rtn >= 0

    def _equip_add(self, equip: Equipment) -> bool:
        """
        Add new equip to self

        Respect to limit_num defined in Equipment subclass
        """

        if not self._equip_check_limit(equip):
            return False

        if self.equip_ensure_require:
            if not equip.check_require(self):
                return False

        self.equip_list.append(equip)
        equip._on_equip(self)
        return True

    def _equip_pop(self, name: str, index: Optional[int] = None) -> Optional[Equipment]:
        """
        Pop the equipment obj.

        name is the index for self.equip_dict
        index is for values in self.equip_dict, default is 0
        """

        stack = self.__get_stack(name)
        if len(stack) == 0:
            return None

        if index is None:
            index = 0
        rtn = stack.pop(index)

        rtn._on_unequip()
        return rtn

    def _equip_tick(self, belong: World) -> None:
        for each in self.equip_list:

            if self.equip_ensure_require:
                if not each.check_require(self):
                    continue

            each._tick(o=self, w=belong)
