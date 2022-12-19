from __future__ import annotations

import pickle
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import (Any, Callable, Dict, List, Optional,
                    Protocol, Self, Tuple, TypeAlias, TypeGuard, TypeVar,
                    runtime_checkable)

from objprint import op
from pydantic import BaseModel

from pyworld.datamodels.function_call import ExceptionModel, RtnStatus


class TickLogModel(BaseModel):
    age: int
    status: RtnStatus = RtnStatus.NOT_SET
    exception_info: Optional[ExceptionModel] = None

    def exception(self, e: Exception) -> None:
        self.status = RtnStatus.FAIL
        self.exception_info = ExceptionModel.from_exception(e)

    def success(self) -> None:
        self.status = RtnStatus.SUCCESS


class Entity:
    """
    Being

    An entity of a world should only be created by World.create_entity() method.
    Because an eid should be taken to create an entity.
    Do not use dataclass as decorate to any Entity or Mixin.

    Subclasses:
        World
        Character
    """

    def __init__(self, *, eid: int = -1) -> None:
        """Entity only accept kwargs arguments."""
        self.__static_called_check: bool = False
        self.__static_init__()
        self.eid = eid
        self.age = 0 
        self.uuid: int = uuid.uuid4().int
        self.report_flag = False

        self.log_flag = False
        self.tick_log: List[TickLogModel] = []
        self.last_tick_log: Optional[TickLogModel] = None

        if not self.__static_called_check:
            raise SyntaxError("Some mixins' __static_init__ methods not call super()!")

    def __static_init__(self) -> None:
        """Will be called when __init__ and loading from pickle bytes.

        All properties start with `_` will be delete when pickling,
        and re-init after un-pickling. Since unpickle processing won't
        run __init__ again, so all the property(cannot be pickled) should
        defined in this method to ensure a proper re-init.

        The save process only happened when tick is done, so all Lock() instance
        is released when pickling.

        Very useful for those property that cannot be pickled."""

        self._tick_lock = Lock()  # Lock when entity is ticking.
        self.__static_called_check = True

    def __eq__(self, other) -> bool:
        if not isinstance(other, Entity):
            return False

        return self.uuid == other.uuid

    def __hash__(self) -> int:
        return self.uuid

    def _tick_last(self, belong: Optional[Entity] = None) -> None:
        """Will do after _tick"""
        pass

    def _tick(self, belong: Optional[Entity] = None) -> None:
        """Describe what a entity should do in a tick.

        Will auto call entity's every (suffix) _tick method.
        """

        with self._tick_lock:
            log = TickLogModel(
                age=self.age,
            )
            try:
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
                log.status = RtnStatus.SUCCESS

            except Exception as e:
                log.exception(e)
            finally:
                self.last_tick_log = log
                if self.log_flag:
                    self.tick_log.append(log)
                self.age += 1


    def _report_tick(self, belong) -> None:
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
        Implement pickle protocol.

        Throw hidden properties named begun with `_`
        which cannot be serialized or jsonable.

        Those non-picklable properties should be set in __static_init__ method
        and will be automatically initiated after loading from binary.
        """

        status = self.__dict__.copy()  # Until now, the entity infomation.
        pop_list: List[str] = []  # Delete list
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
# Tick Method Type that would be called in future.

Entities = TypeVar("Entities", bound=Entity)
# All subclasses of the Entity


class ConcurrentMixin(Entity):
    """
    Add the ability that Entity could running concurrent ticks.
    Module will run every FutureTick in self.__concurrent_pending after
    other tick is done.
    """

    def __static_init__(self) -> None:
        super().__static_init__()
        self.__pending: List[Tuple[FutureTick, Entity]] = []

    def _concurrent_tick_add(self, owner: Entity, method: FutureTick) -> None:
        """
        When need to run a tick in the future, using this method.

        `owner` will be passed as `self` argument into method.
        """

        self.__pending.append((method, owner))

    def _tick_last(self, belong: Optional[Entity] = None) -> None:
        """
        Override the Entity._tick_last method.

        Run all the FutureTick instance in self.__pending list
        after a _tick is done.
        """

        super()._tick_last(belong)

        # If no pending, just pass.
        if self.__pending == []:
            return

        # Else, run every pending tick in pool
        with ThreadPoolExecutor(max_workers=16) as exe:
            future_list: list[Future[None]] = [
                exe.submit(*tick, belong) for tick in self.__pending
            ]

        self.__pending = []  # clear up

        for future in future_list:
            future.result()  # wait for every future is done


@runtime_checkable
class Checkable(Protocol):
    @classmethod
    def check(cls, obj: Entity) -> TypeGuard[Self]:
        ...
