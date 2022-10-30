"""
Item class and CargoMixin

Item class and CargoMixin are important parts of pyworld.
These system provide different 'abilities' for different instances.
"""
from __future__ import annotations
from typing import List, Optional, Iterable, Dict
from dataclasses import dataclass, field
from threading import Lock
from collections import UserDict

from pyworld.world import Character, World


@dataclass
class Item():
    """
    A very simple and light class, only used in cargo system.

    Item could only exist in a cargo.

    Like entity, item also influenced by world `tick`.
    """
    mass: float = field(default=0, init=False)

    def __post_init__(self):
        self.name: str = self.__class__.__name__
        self.type: type = self.__class__

    def to_stack(self) -> ItemStack:
        """Use self to create a itemstack."""
        return ItemStack([self])

    def tick(self, o: CargoContainer, w: World):
        """Will be called every tick."""
        pass


@dataclass
class ItemStack(Item):  # TODO: Heritage Item, cargo could both have Item and ItemStack!
    """One virtual container
    Contain items that have the same name.
    WITH NO NUMBER LIMIT"""

    item_list: List[Item]

    def __post_init__(self):
        super().__post_init__()
        self.item_name = str(self.item_list[0].name)
        assert all((item.name == self.item_name) for item in self.item_list), \
            TypeError("Names of items in item list is not same.[{}]".format(
                self.item_list
                )
            )

    def split(self, num: int) -> ItemStack:
        """Split self ItemStack into two, return the other."""
        if num >= len(self):
            raise IndexError('Index out of length.')
        else:
            other = self.item_list[:num]
            self.item_list = self.item_list[num:]
            return other

    @property
    def mass(self):
        return sum(item.mass for item in self.item_list)

    def tick(self, o: CargoMixin, w: World) -> None:
        for item in self.item_list:
            item.tick(o=o, w=w)

    def __len__(self):
        return len(self.item_list)

    def __add__(self, other) -> ItemStack:
        self.item_list += other.item_list
        other.item_list = []
        return self

    def __iter__(self) -> List[Item]:
        return self.item_list

    # HACK: Find a better way to get itemstack.item_list[0]
    def __getitem__(self, key: int) -> Item:
        return self.item_list[key]


class CargoContainer(UserDict):  # type: Dict[str, ItemStack]
    """Use as the container to store all items."""
    def __init__(self, *stacks: Iterable[ItemStack]):
        super().__init__()
        for stack in stacks:
            assert isinstance(stack, ItemStack)
            self.append(stack)

    def append(self, stack: ItemStack) -> None:
        name = stack.item_name
        if name in self.keys():
            self.data[name] += stack
        else:
            self.data[name] = stack

    @property
    def mass(self):
        return sum(
            (
                stack.mass for stack in self.data.values()
            )
        )

    def __getattr__(self, name: str):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return self.data[name]

    def __setattr__(self, name, value) -> None:
        if name == 'data':
            super().__setattr__(name, value)
        else:
            self.data[name] = value

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

    def cargo_has_slot(self) -> bool:
        """Return the cargo wether has empty space"""
        if self.cargo_max_slots < 0:  # minus zero slots always True
            return True
        else:
            if len(self.cargo) < self.cargo_max_slots:
                return True
            else:
                return False

    def cargo_add_itemstack(self, item_stack: ItemStack) -> bool:
        """
        Use this method to add item stack onto one's cargo.
        Once the itemstack is added to the entity instance,
        you can fetch the itemstack by using .cargo_xxx property.

        Return True if success.
        """
        with self.__cargo_lock:
            if self.cargo_has_slot():
                self.cargo.append(item_stack)
                return True
            else:
                return False

    def cargo_pop_itemstack(self, index: int) -> Optional[ItemStack]:
        """
        Pop out the index of cargo.
        Also delete the cargo_<itemstack> property of the itemstack

        Return the stack if success. Other return is None.
        """
        with self.__cargo_lock:

            if index <= len(self.cargo):
                stack = self.cargo.pop(index)
                return stack
            else:
                return None

    def cargo_tick(self, belong: World):
        """Tick every itemstack and item."""
        with self.__cargo_lock:
            for itemstack in self.cargo:
                itemstack.tick(o=self, w=belong)


class Radar(Item):
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

    def radar_tick(self, o: CargoMixin, w: World):
        if self.auto_scan:
            if o.age % self.interval_tick == 0:
                self.scan_result = w.world_get_nearby_character(
                    char=o, radius=self.radius
                )
                self.last_update = w.age
