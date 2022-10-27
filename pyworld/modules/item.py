from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass
from threading import Lock

from pyworld.world import Character, World


@dataclass
class Item:
    """Only used in cargo system.

    Like entity, item also has 'tick' method.
    Item could only exist in a cargo.
    """

    # TODO: Add item entity so that item could exist in continuum.

    def __post_init__(self):
        self.name: str = self.__class__.__name__
        self.type: type = self.__class__

    def to_stack(self) -> ItemStack:
        """Use self to create a itemstack."""
        return ItemStack([self])

    def tick(self, o: CargoMixin, w: World):
        """Every item instance should implements this func."""
        raise NotImplementedError


@dataclass
class ItemStack:
    """One virtual container"""

    item_list: List[Item]
    item_name: str = "None"

    def __post_init__(self):
        self.item_name = str(self.item_list[0].item_name)

    def __add__(self, other) -> ItemStack:
        self.item_list += other.item_list
        return self

    def __iter__(self) -> List[Item]:
        return self.item_list

    def tick(self, o: CargoMixin, w: World) -> None:
        for item in self.item_list:
            item.tick(o=o, w=w)


class CargoMixin(Character):
    """Cargo"""

    def __init__(self, *args, cargo_max_slots: int = 0, **kwargs) -> None:
        """Parameter cargo_max_slots determins the max slots(ItemStack)
        that a cargo could have.

        If a sub-zero cargo_max_slots is give, cargo is infinite.
        """
        super().__init__(*args, **kwargs)
        self.cargo_list: List[ItemStack] = []
        self.cargo_max_slots = cargo_max_slots

    def __static_init__(self):
        super().__static_init__()
        self.__cargo_lock = Lock()

    def cargo_has_slot(self) -> bool:
        """Return the cargo wether has empty space"""
        if self.cargo_max_slots < 0:  # minus zero slots always True
            return True
        else:
            if len(self.cargo_list) < self.cargo_max_slots:
                return True
            else:
                return False

    def cargo_add_itemstack(self, item_stack: ItemStack) -> bool:
        """Use this method to add item stack onto one's cargo.

        Return True if success."""
        with self.__cargo_lock:
            if self.cargo_has_slot():
                self.cargo_list.append(item_stack)
                return True
            else:
                return False

    def cargo_pop_itemstack(self, index: int) -> Optional[ItemStack]:
        """Pop out the index of cargo."""
        with self.__cargo_lock:
            if index <= len(self.cargo_list):
                stack = self.cargo_list.pop(index)
                return stack
            else:
                return None

    def cargo_tick(self, belong: World):
        """Tick every itemstack and item."""
        with self.__cargo_lock:
            for itemstack in self.cargo_list:
                itemstack.tick(o=self, w=belong)


class Radar(Item):
    def __init__(
        self,
        *args,
        radius: int,
        interval_tick: int = 100,
        auto_scan: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.radius = radius
        self.interval_tick = interval_tick
        self.auto_scan = auto_scan
        self.scan_result: List[Character] = []

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

    def tick(self, o: CargoMixin, w: World):
        if self.auto_scan:
            if o.age % self.interval_tick == 0:
                self.scan_result = w.world_get_nearby_character(
                    char=o, radius=self.radius
                )
# TODO: Test needed
