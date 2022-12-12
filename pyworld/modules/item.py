"""
Item class and CargoMixin

Item class and CargoMixin are important parts of pyworld.
These system provide different 'abilities' for different instances.
"""

from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, ClassVar, Dict, Generic, Optional, Self, Type, TypeVar

from pyworld.control import ControlMixin, ControlResultModel
from pyworld.datamodels.function_call import RequestModel
from pyworld.world import Character, World


@dataclass
class Item:
    """
    Item Interface Usage

    Item is a stateless class that only handle the _tick method and static
    properties. If an Item must implement complicate method, use its ItemStack
    to storage the dynamic method.

    Every subclass of Item(let's call it Items) is a singleton,
    stored in Item.all_items.

    Properties:
    - all_items: ClassVar, storage all singleton of subclass items
    - name: the name of the item. Proxy to Self.__class__.__name__
    - mass: Must defined in subclass, a __post_init__ function would check it.

    Methods: See docs below.
    """

    all_items: ClassVar[Dict[str, Any]] = field(default_factory=dict)
    # all_items storage all singleton of item

    mass: int = field(default=0, init=False)
    # item must have mass interface

    def __new__(cls: Type[Items]) -> Items:
        """All item's subclass is singleton."""

        name: str = cls.__name__
        if name not in Item.all_items:
            Item.all_items[name] = super(Item, cls).__new__(cls)
        return Item.all_items[name]

    def __post_init__(self) -> None:
        assert self.mass > 0, NotImplementedError("Item class must have mass")

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def to_stack(self, num: int = 1) -> ItemStack[Self]:
        return ItemStack(item=self, num=num)

    def _tick(self, o: CargoMixin[Items], w: World) -> None:
        """Item could has _tick method"""
        pass


Items = TypeVar("Items", bound=Item)  # All the subclass of Item


@dataclass
class ItemStack(Generic[Items]):
    """
    It is a stack of one same item.

    Properties:
        name: return first item's name in data list
        mass: return summary mass of all item in data list

    """

    item: Items
    num: int = 1

    @property
    def name(self) -> str:  # Return the Item type name
        return self.item.name

    @property
    def mass(self) -> int:
        return self.num * self.item.mass

    def _gather(self, o: ItemStack[Items]) -> Self:
        if o.item is not self.item:
            raise TypeError(
                f"Cannot add two different[{self.item}, {o.item}] ItemStack."
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
    Use as the container to store all ItemStack

    A cargo would process ItemStack follow these orders:
    1. Only ItemStack could storage into cargo.
    2. Stack same ItemStack, as more as possible.

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

    def __init__(self, *thing: ItemStack[Items]) -> None:
        super().__init__()
        for i in thing:
            self._append(i)

    @property
    def mass(self) -> int:
        return sum((stack.mass for stack in self.data.values()))

    @property
    def count(self) -> int:
        return sum((i.num for i in self.values()))

    def _append(self, o: ItemStack[Items]) -> None:
        for name in self.data:
            if name == o.name:
                # if: Cargo already has the same-named ItemStack
                self.data[name]._gather(o)
                return

        # else: Cargo not yet has the same-named ItemStack
        self.data[o.name] = o
        return

    def _pop(self, key: str) -> Optional[ItemStack[Items]]:
        return self.data.pop(key, None)


class CargoMixin(Character, Generic[Items]):
    """Add Cargo ability to an Character"""

    def __init__(self, cargo_max_slots: int = 0, **kwargs) -> None:
        """Parameter cargo_max_slots determines the max slots(ItemStack)
        that a cargo could have.

        If a sub-zero cargo_max_slots is give, cargo is infinite.
        """
        super().__init__(**kwargs)
        self.cargo: Cargo[Items] = Cargo()
        self.cargo_max_slots: int = cargo_max_slots

    def __static_init__(self) -> None:
        super().__static_init__()
        self.__cargo_lock: Lock = Lock()

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
            stack = self.cargo._pop(name)
            return stack

    def _cargo_tick(self, belong: World):
        """Tick every itemstack and item."""
        with self.__cargo_lock:
            for itemstack in self.cargo.values():
                itemstack.item._tick(o=self, w=belong)
