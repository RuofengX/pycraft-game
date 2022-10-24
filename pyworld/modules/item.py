from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass

from pyworld.world import Character, Entity


@dataclass
class Item(Entity):
    """Non-Character entity.

    No position related thing.
    Still needs to be create by a world."""
    def __post_init__(self):
        self.item_name = self.__class__.__name__
        self.item_type = self.__class__

    def to_stack(self) -> ItemStack:
        """Use self to create a itemstack."""
        return ItemStack([self])


@dataclass
class ItemStack():
    """One virtual container"""
    item_list: List[Item]
    item_name: str = 'Item'

    def __post_init__(self):
        self.item_name = str(self.item_list[0].item_name)

    def __add__(self, other) -> ItemStack:
        self.item_list += other.item_list
        return self

    def __iter__(self) -> List[Item]:
        return self.item_list


class CargoMixin(Character):
    """Cargo"""
    def __init__(self, *args, cargo_max_slots: int, **kwargs) -> None:
        """Parameter cargo_max_slots determins the max slots(ItemStack)
        that a cargo could have.

        If a sub-zero cargo_max_slots is give, cargo is infinite.
        """
        super().__init__(*args, **kwargs)
        self.cargo_list: List[ItemStack] = []
        self.cargo_max_slots = cargo_max_slots

    @property
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
        if self.cargo_has_slot:
            self.cargo_list.append(item_stack)
            return True
        else:
            return False

    def cargo_release_itemstack(self, index: int) -> ItemStack:
        return self.cargo_list.pop(index)

    def cargo_pick_itemstack(self, item_name: str) -> Optional[ItemStack]:
        """Return the first itemstack that match the item_name.
        Return None if no matching."""
        for i in range(len(self.cargo_list)):
            stack = self.cargo_list[i]
            if stack.item_name == item_name:
                return stack
        return None


class BatteryMixin(Character):
    """AAA"""
    pass
