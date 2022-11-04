from __future__ import annotations
from typing import List, TYPE_CHECKING, TypeVar
import uuid

from objprint import op  # type: ignore

if TYPE_CHECKING:
    from pyworld.world import World


class Entity:
    """Being

    An entity of a world should only be created by World.create_entity() method.
    Because an eid should be taken to create an entity.
    Do not use dataclass as decorate to any Entity or Mixin.

    Subclasses:
        World
        Character
    """

    def __init__(self, *, eid: int = -1):
        """Entity type only accept kwargs argumetns."""
        self.__static_init__()
        self.eid = eid
        self.age = 0
        self.uuid: int = uuid.uuid4().int
        self.report_flag = False

    def __static_init__(self):
        """Will be called when __init__ and loading from pickle bytes.

        All data defined here will be drop when pickling,
        and re-set after un-pickling.

        Very useful for those property that cannot be pickled."""
        pass

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.uuid == other.uuid
        else:
            return False

    def tick(self, belong: None | World = None) -> None:
        """Describe what a entity should do in a tick."""
        self.age += 1
        self.uuid = uuid.uuid4().int
        if self.report_flag:
            self.report()

        # Call every function named after _tick of class
        for func in dir(
            self
        ):  # dir() could show all instance method; __dict__ only returns properties.
            if func[-5:] == "_tick":
                getattr(self, func)(belong)

    def report(self) -> None:
        """Report self, for logging or debuging usage."""
        if self.age % 20 == 0:
            print('-' * 10)
            op(self.__dict__)

    def __getstate__(self) -> dict:
        """Get every that matters,

        Throw hidden things like _thread.Lock(),
        which cannot be serialized or jsonable.

        Those ugly properties should be set in __static_init__ method
        and will be automatically initiate by __init__ method."""
        status = self.__dict__.copy()
        pop_list: List[str] = []
        for key in status.keys():
            if key[0] == '_':
                pop_list.append(key)
        for key in pop_list:
            status.pop(key)
        return status

    def __setstate__(self, state: dict) -> None:
        self.__dict__.update(state)
        self.__static_init__()


if TYPE_CHECKING:
    Entities = TypeVar('Entities', bound=Entity)
