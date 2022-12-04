"""
Item class and CargoMixin

Item class and CargoMixin are important parts of pyworld.
These system provide different 'abilities' for different instances.
"""

from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, List, Optional, final, Dict

from pyworld.world import Character, World
from pyworld.control import ControlMixin, ControlResult


@dataclass
class CargoBase:
    """
    Generate instance that could be added into CargoMixin.

    Properties:
        name: Name of the thing.

    Methods:
        tick
    """

    def __post_init__(self):
        self.name = self.__class__.__name__

    def _tick(self, o: CargoMixin, w: World):
        pass


@dataclass
class ItemBase(CargoBase):
    """
    Extend CargoThing with to_stack() function and mass property.
    """

    mass: float = field(default=0, init=False)
    num: int = field(default=1, init=False)

    def to_stack(self):
        return ItemStack(data=[self])


@final
@dataclass
class ItemStack(CargoBase):
    """
    Final class, item stack.
    ItemStack it self will not ensure the items in the stack
    is the same item.

    Properties:
        data: list of container
        name: return first item's name in data list
        mass: return summary mass of all item in data list

    """
    data: List[ItemBase]

    def __post_init__(self):
        """Override the name getter."""
        self.name = self.data[0].name

    @property
    def mass(self):
        return sum(
            (i.mass for i in self.data)
        )

    def __add__(self, o: ItemStack) -> ItemStack:
        if o.name != self.name:
            raise TypeError(
                f'Cannot add two different[{self.name}, {o.name}] CargoThing.'
            )
        return ItemStack(
            self.data + o.data
        )

    def __radd__(self, o: ItemStack):
        if o.name != self.name:
            raise TypeError(
                f'Cannot add two different[{self.name}, {o.name}] CargoThing.'
            )
        else:
            self.data += o.data


class CargoContainer(ControlMixin, UserDict):
    """
    Use as the container to store all CargoThing

    Type: Dict[CargoThing]

    Properties:
        data: dict for inner data.
        mass: total mass include all thing in self
        count: summary num of things in self

    Methods:
        append: add new thing into cargo
        __iter__: return generator of self.values()

    Notes:
        proxy behavior: any dot properties getter will be proxy to
                        the [] function.

    """

    def __init__(self, *items: CargoBase):
        super().__init__()
        for item in items:
            self.append(item)

    def append(self, o: CargoBase):
        name = o.name
        if name in self:
            self.data[name] += o
        else:
            self.data[name] = o
            setattr(self, name, self.data[name])

    def pop(self, key: str, default: Optional[Any] = None):
        super().pop(key, default)
        delattr(self, key)

    @property
    def mass(self):
        return sum(
            (
                stack.mass for stack in self.data.values()
            )
        )

    @property
    def count(self) -> int:
        return sum(
            (i.num for i in self)
        )

    def __iter__(self):
        return (_ for _ in self.data.values())


class CargoMixin(Character):
    """Cargo"""

    def __init__(self, cargo_max_slots: int = 0, **kwargs) -> None:
        """Parameter cargo_max_slots determines the max slots(ItemStack)
        that a cargo could have.

        If a sub-zero cargo_max_slots is give, cargo is infinite.
        """
        super().__init__(**kwargs)
        self.cargo = CargoContainer()
        self.cargo_max_slots = cargo_max_slots

    def __static_init__(self):
        super().__static_init__()
        self.__cargo_lock = Lock()

    def cargo_list_method(self) -> Dict[str, str]:
        return self.cargo.ctrl_list_method()

    def cargo_list_property(self) -> Dict[str, Any]:
        return self.cargo.ctrl_list_property()

    def cargo_safe_call(self, func_name: str, **kwargs) -> ControlResult:
        return self.cargo.ctrl_safe_call(func_name, **kwargs)

    def cargo_has_slot(self) -> bool:
        """Return whether the cargo has empty space."""
        if self.cargo_max_slots < 0:  # minus zero slots always True
            return True
        else:
            if len(self.cargo) < self.cargo_max_slots:
                return True
            else:
                return False

    def _cargo_add(self, cb: CargoBase) -> bool:
        """
        Use this method to add item stack onto one's cargo.
        Once the itemstack is added to the entity instance,
        you can fetch the itemstack by using .cargo_xxx property.

        Return True if success.
        """

        with self.__cargo_lock:
            if self.cargo_has_slot():
                self.cargo.append(cb)
                return True
            else:
                return False

    def _cargo_pop(self, name: str) -> Optional[CargoBase]:
        """
        Pop out the index of cargo.
        Also delete the cargo_<itemstack> property of the itemstack

        Return the stack if success. Other return is None.
        """
        if name not in self.cargo:
            return None

        with self.__cargo_lock:
            stack = self.cargo.pop(name)
            return stack

    def _cargo_tick(self, belong: World):
        """Tick every itemstack and item."""
        with self.__cargo_lock:
            for c_thing in self.cargo:
                c_thing._tick(o=self, w=belong)


class Radar(ItemBase):
    def __init__(
        self,
        radius: int = 0,
        interval_tick: int = 100,
        auto_scan: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.radius = radius
        self.interval_tick = interval_tick
        self.auto_scan = auto_scan
        self.scan_result: List[Character] = []
        self.last_update: int = -1

    def set_scan_tick(self, interval: int):
        self.interval_tick = interval

    def toggle_auto_scan(self, target: Optional[bool] = None):
        """Toggle radio auto_scan
        If target: bool is given, set auto_scan to target status
        """
        if target is None:
            self.auto_scan = not self.auto_scan
        else:
            self.auto_scan = target

    def _tick(self, o: CargoMixin, w: World):
        if self.auto_scan:
            if o.age % self.interval_tick == 0:  # use the interval
                self.characters_list = w.world_get_nearby_character(
                    char=o, radius=self.radius
                )
                self.last_update = w.age
