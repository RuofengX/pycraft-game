from __future__ import annotations

import pickle
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock, Thread
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    Self,
    Type,
    TypeAlias,
    TypeGuard,
    TypeVar,
    runtime_checkable,
)

from objprint import op  # type:ignore[import]


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
        self.__isolate_list: List[Thread] = []
        self.__static_called_check: Literal[True] = True

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.uuid == other.uuid
        else:
            return False

    def __hash__(self) -> int:
        return self.uuid

    def _tick_last(self, belong: Optional[Entity] = None) -> None:
        """Will do after _tick"""
        raise NotImplementedError()

    def _tick(self, belong: Optional[Entity] = None) -> None:
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
                        target: Callable[[Optional[Entity]], None] = getattr(self, func)
                        if callable(target):
                            target(belong)

            self._tick_last(belong)

    def _report(self) -> None:
        """Report self, for logging or debugging usage."""
        if self.age % 20 == 0:
            op(self.__dict__)

    def get_state(self) -> Dict[str, Any]:
        """Return the entity state dict."""
        return self.__getstate__()

    def get_state_b(self) -> bytes:
        """Return the entity pickle binary."""
        return pickle.dumps(self)

    def __getstate__(self) -> Dict[str, Any]:
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
            if key[0] == "_":
                pop_list.append(key)
        for key in pop_list:
            status.pop(key)
        return status

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.__static_init__()


FutureTick: TypeAlias = Callable[[Entity, Optional[Entity]], None]


class ConcurrentMixin(Entity):
    """
    Add the ability that Entity could running concurrent ticks.
    Module will run every FutureTick in self.__concurrent_pending after
    other tick is done.
    """

    def __static_init__(self) -> None:
        super().__static_init__()
        self.__pending: List[FutureTick] = []

    def _concurrent_tick_add(self, method: FutureTick) -> None:
        """When need running a _concurrent_tick, using this method."""
        self.__pending.append(method)

    def _tick_last(self, belong: Optional[Entity] = None) -> None:
        """Override the Entity._tick_last method."""

        super()._tick_last(belong)

        if self.__pending == []:  # If no pending, just pass.
            return

        # Else, run every pending tick in pool
        with ThreadPoolExecutor(max_workers=16) as exe:
            future_list: list[Future[None]] = [
                exe.submit(tick, self, belong) for tick in self.__pending
            ]

        self.__pending = []  # clear up

        for future in future_list:
            future.result()  # wait for every future is done


Entities = TypeVar("Entities", bound=Entity)


@runtime_checkable
class CheckableProtocol(Protocol):
    @classmethod
    def check(cls, obj: Entity) -> TypeGuard[Type[Self]]:
        ...
