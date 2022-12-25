from __future__ import annotations

import pickle
import uuid
from _thread import LockType
from concurrent.futures import Future, ThreadPoolExecutor
from functools import wraps
from threading import Lock
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    Dict,
    List,
    Optional,
    ParamSpec,
    Protocol,
    Self,
    Set,
    Tuple,
    TypeAlias,
    TypeGuard,
    TypeVar,
    runtime_checkable,
)

from objprint import op
from pydantic import BaseModel

from pyworld.basic import Pickleable
from pyworld.datamodels.function_call import ExceptionModel
from pyworld.datamodels.status_code import CallStatus

if TYPE_CHECKING:
    from pyworld.world import World


Self_Entity = TypeVar("Self_Entity", bound="Entity")
T = TypeVar("T")
P = ParamSpec("P")


def with_instance_lock(lock_name: str, debug: bool = False):
    """
    Used in Entity's method define, return a decorate:

    The raw func's first args must be Entities type.
    Will auto require the instance's lock by given name, then run the raw func.

    """

    def has_lock(target: Entity, lock_name: str) -> Optional[LockType]:
        if hasattr(target, lock_name):
            lock = getattr(target, lock_name)
            if isinstance(lock, LockType):
                return lock
        else:
            if debug:
                raise AttributeError(
                    f"Instance of {target.__class__.__name__} "
                    "do not have {lock_name} lock."
                )
            return None

    def run_with_lock(func: Callable[Concatenate[Self_Entity, P], Any]):
        @wraps(func)
        def inner(self: Self_Entity, *args: P.args, **kwargs: P.kwargs) -> Any:
            lock = has_lock(self, lock_name)
            if lock is None:
                return func(self, *args, **kwargs)
            else:
                with lock:
                    return func(self, *args, **kwargs)

        return inner

    return run_with_lock


class TickLogModel(BaseModel):
    age: int
    status: CallStatus = CallStatus.INIT
    exception_info: Optional[ExceptionModel] = None

    def exception(self, e: Exception) -> Self:
        self.status = CallStatus.FAIL
        self.exception_info = ExceptionModel.from_exception(e)
        return self

    def success(self) -> Self:
        self.status = CallStatus.SUCCESS
        return self


class Entity(Pickleable):
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
        super().__init__()
        self.eid = eid
        self.age = 0
        self.uuid: int = uuid.uuid4().int

        self.tick_log: List[Dict[str, Any]] = []
        self.last_tick_log: Optional[Dict[str, Any]] = None

    def __static_init__(self) -> None:

        self._tick_lock = Lock()  # Lock when entity is ticking.
        self._report_flag = (
            False  # Control whether show a message about self in console.
        )
        self._log_flag = False  # Control whether write log into self.tick_log
        self._world: Optional[World] = None

        # name of additional attrs that wouldn't show to user.
        self._dir_mask: Set[str] = set()

        return super().__static_init__()

    def get_state(self) -> Dict[str, str]:
        """Return the entity state dict."""
        return {k: str(v) for k, v in self.__getstate__().items()}
        # return self.__getstate__()

    def get_state_b(self) -> bytes:
        """Return the entity pickle binary."""
        return pickle.dumps(self)

    def _tick_first(self, belong: Optional[World]) -> None:
        """
        Will do before _tick
        Useful for basic class to prepare data before subclass custom tick.

        e.g. Equipment class use _tick_first to refresh EquipStatus for later
        use in subclasses.
        """

        pass

    def _tick_last(self, belong: Optional[World] = None) -> None:
        """
        Will do after _tick
        Useful for basic class to collection data after subclass custom tick.

        e.g. ConcurrentMixin use _tick_last to gather and wait for all async
        tick finished.
        """
        pass

    @with_instance_lock("_tick_lock")
    def _tick(self, belong: Optional[World] = None) -> None:
        """
        Describe what a entity should do in a tick.

        Will auto call entity's every (suffix) _tick method.
        """

        self._world = belong
        log = TickLogModel(
            age=self.age,
        )
        try:
            # BEFORE
            self._tick_first(belong)

            # MAIN::Call every function named after _tick of class
            for func in dir(
                self
            ):  # dir() could show all instance method and properties;
                # __dict__ only returns properties.
                if len(func) > 5:  # not _tick itself
                    if func[-5:] == "_tick":  # named after _tick
                        target: Callable[[Optional[Entity]], None] = getattr(self, func)
                        if callable(target):
                            target(belong)
            # AFTER
            self._tick_last(belong)
            self.last_tick_log = log.success().dict()

        except Exception as e:
            self.last_tick_log = log.exception(e).dict()
        finally:
            if self._log_flag:
                self.tick_log.append(log.dict())
            self.age += 1

    def _report_tick(self, belong: World) -> None:
        """Report self, for logging or debugging usage."""
        if not self._report_flag:
            return
        if self.age % 20 == 0:
            op(self.__dict__)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Entity):
            return False

        return self.uuid == other.uuid

    def __hash__(self) -> int:
        return self.uuid

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.uuid}>"


FutureTick: TypeAlias = Callable[[Entity, Optional[Entity]], None]
# Tick Method Type that would be called in future.

Entities = TypeVar("Entities", bound=Entity)
Entities_co = TypeVar("Entities_co", bound=Entity, covariant=True)
Entities_con = TypeVar("Entities_con", bound=Entity, contravariant=True)
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

    def _tick_last(self, belong: Optional[World] = None) -> None:
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
