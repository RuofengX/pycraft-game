from __future__ import annotations
from typing import List, TYPE_CHECKING, TypeVar
import uuid
import pickle
from threading import Lock

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
        """Entity type only accept kwargs arguments."""
        self.__static_init__()
        self.eid = eid
        self.age = 0
        self.uuid: int = uuid.uuid4().int
        self.report_flag = False
        if not self.__static_called_check:
            raise SyntaxError("Some mixins' __static_init__ methods not call super()!")

    def __static_init__(self):
        """Will be called when __init__ and loading from pickle bytes.

        All data defined here will be drop when pickling,
        and re-set after un-pickling.

        Very useful for those property that cannot be pickled."""
        self._tick_lock = Lock()
        self.__static_called_check = True

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.uuid == other.uuid
        else:
            return False

    def __hash__(self):
        return self.uuid

    def _tick(self, belong: None | World = None) -> None:
        """Describe what a entity should do in a tick."""

        with self._tick_lock:
            self.age += 1
            if self.report_flag:
                self._report()

            # Call every function named after _tick of class
            for func in dir(
                self
            ):  # dir() could show all instance method and properties;
                # __dict__ only returns properties.
                if len(func) > 5:  # not _tick itself
                    if func[-5:] == "_tick":  # named after _tick
                        getattr(self, func)(belong)

    def _report(self) -> None:
        """Report self, for logging or debugging usage."""
        if self.age % 20 == 0:
            op(self.__dict__)

    def get_state(self) -> dict:
        """Return the entity state dict."""
        return self.__getstate__()

    def get_state_b(self) -> bytes:
        """Return the entity pickle binary."""
        return pickle.dumps(self)

    def __getstate__(self) -> dict:
        """
        Get everything that matters,

        Throw hidden things like _thread.Lock(),
        which cannot be serialized or jsonable.

        Those non-picklable properties should be set in __static_init__ method
        and will be automatically initiate by __init__ method.
        """

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
