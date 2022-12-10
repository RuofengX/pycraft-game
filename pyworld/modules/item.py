"""
Item class and CargoMixin

Item class and CargoMixin are important parts of pyworld.
These system provide different 'abilities' for different instances.
"""

from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass, field
from threading import Lock
from typing import (
    Any,
    List,
    Optional,
    final,
    Dict,
    ClassVar,
    TypeVar,
    Type,
    Generic,
    Self,
)

from pyworld.world import Character, World
from pyworld.control import ControlMixin, ControlResultModel
from pyworld.datamodels.function_call import RequestModel


class CargoThing:
    """Things that could get stored in cargo"""

    pass


class ItemMeta(type):
    """All items are singleton, stored in Item.all_items"""

    def __new__(cls, name, bases, attrs):

        if attrs["mass"] is None:
            raise NotImplementedError("Item class must have mass")

        return type.__new__(cls, name, bases, attrs)


@dataclass
class Item(metaclass=ItemMeta):
    all_items: ClassVar[Dict[str, Any]] = field(default_factory=dict)
    # all_items storage all singleton of item

    mass: Optional[int] = field(default=None, init=False)
    # item must have mass interface

    def __new__(cls: Type[Items]) -> Items:
        """All item's subclass is singleton."""

        name = cls.__class__.__name__
        if name not in Item.all_items:
            Item.all_items[name] = super(Item, cls).__new__(cls)
        return Item.all_items[name]

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def _tick(self, o: CargoMixin[Items], w: World[Character]):
        """Item could has _tick method"""
        pass


Items = TypeVar("Items", bound=Item)  # All the subclass of Item


@final
@dataclass
class ItemStack(Generic[Items]):
    """
    Final class, item stack.
    It is a stack of one same item.

    Properties:
        name: return first item's name in data list
        mass: return summary mass of all item in data list

    """

    item: Items
    num: int = 1

    @property
    def mass(self):
        return self.item.mass * self.num

    @property
    def name(self):  # actually same as the item
        return self.item.name

    def _gather(self, o: ItemStack[Items]) -> Self:  # type: ignore[valid-type]
        if o.item is not self.item:
            raise TypeError(
                f"Cannot add two different[{self.item}, {o.item}] CargoThing."
            )
        self.num += o.num
        o.num = 0
        return self

    def _split(self, num: int) -> ItemStack[Items]:
        if num > self.num:
            return ItemStack(item=self.item, num=0)
        else:
            self.num -= num
            return ItemStack(item=self.item, num=num)


class Cargo(ControlMixin, UserDict[str, ItemStack[Items]]):
    """
    Use as the container to store all CargoThing

    Properties:
        data: dict for inner data.
        mass: total mass include all thing in self

    Methods:
        append: add new thing into cargo
        __iter__: return generator of self.values()

    Notes:
        proxy behavior: any dot properties getter will be proxy to
                        the [] function.

    """

    def __init__(self, *itemstacks: ItemStack[Items]):
        super().__init__()
        for i in itemstacks:
            self._append(i)

    @property
    def mass(self):
        return sum((stack.mass for stack in self.data.values()))

    @property
    def count(self) -> int:
        return sum((i.num for i in self))

    def _append(self, o: ItemStack[Items]) -> None:
        # Cargo already has the same-named ItemStack
        for name in self.data:
            if name == o.name:
                self.data[name]._gather(o)
                return

        # Cargo not yet has the same-named ItemStack
        self.data[name] = o
        return

    def _pop(self, key: str) -> Optional[ItemStack[Items]]:
        return self.data.pop(key, None)

    def __iter__(self):
        return self.data


# FIXME: STOP AT HERE, CHECK BELOW
class CargoMixin(Character, Generic[Items]):
    """Cargo"""

    def __init__(self, cargo_max_slots: int = 0, **kwargs) -> None:
        """Parameter cargo_max_slots determines the max slots(ItemStack)
        that a cargo could have.

        If a sub-zero cargo_max_slots is give, cargo is infinite.
        """
        super().__init__(**kwargs)
        self.cargo: Cargo[Items] = Cargo()
        self.cargo_max_slots = cargo_max_slots

    def __static_init__(self):
        super().__static_init__()
        self.__cargo_lock = Lock()

    def cargo_list_method(self) -> Dict[str, str]:
        return self.cargo.ctrl_list_method()

    def cargo_list_property(self) -> Dict[str, Any]:
        return self.cargo.ctrl_list_property()

    def cargo_safe_call(self, data: RequestModel) -> ControlResultModel:
        return self.cargo.ctrl_safe_call(data)

    def cargo_has_slot(self) -> bool:
        """Return whether the cargo has empty space."""
        if self.cargo_max_slots < 0:  # minus zero slots always True
            return True
        else:
            if len(self.cargo) < self.cargo_max_slots:
                return True
            else:
                return False

    def _cargo_add(self, itemstack: ItemStack[Items]) -> bool:
        """
        Use this method to add item stack onto one's cargo.
        Once the itemstack is added to the entity instance,
        you can fetch the itemstack by using .cargo_xxx property.

        Return True if success.
        """

        with self.__cargo_lock:
            if self.cargo_has_slot():
                self.cargo._append(itemstack)
                return True
            else:
                return False

    def _cargo_pop(self, name: str) -> Optional[ItemStack[Items]]:
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

    def _cargo_tick(self, belong: World[Character]):
        """Tick every itemstack and item."""
        with self.__cargo_lock:
            for c_thing in self.cargo:
                c_thing._tick(o=self, w=belong)


class Radar(Item):
    def __init__(
        self,
        *,
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

    def _tick(self, o: CargoMixin[Items], w: World[Character]):
        if self.auto_scan:
            if o.age % self.interval_tick == 0:  # use the interval
                self.characters_list = w.world_get_nearby_character(
                    char=o, radius=self.radius
                )
                self.last_update = w.age
