from __future__ import annotations
from typing import List, TypeVar, Type
import uuid

from objprint import op  # type: ignore


class Entity:
    """Being

    An entity of a world should only be created by World.create_entity() method.
    Because an eid should be taken to create an entity.
    """

    def __init__(self, eid: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__static_init__()
        self.eid = eid
        self.age = 0
        self.uuid: int = uuid.uuid4().int
        self.report_flag = False

    def __static_init__(self):
        """Will be called when loading from pickle bytes."""
        pass

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.uuid == other.uuid
        else:
            return False

    def tick(self, belong: Entity = None):
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
                getattr(self, func)(belong=belong)

    def report(self):
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


Entities = TypeVar("Entities", bound=Type[Entity])
