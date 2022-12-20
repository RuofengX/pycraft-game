from __future__ import annotations

from functools import wraps
from threading import Lock, Thread
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Protocol,
    Type,
    TypeGuard,
    cast,
    runtime_checkable,
)

from pyworld.basic import Vector
from pyworld.entity import (
    ConcurrentMixin,
    Entities,
    Entity,
    FutureTick,
    with_instance_lock,
)

if TYPE_CHECKING:
    from pyworld.player import Player


def mark_isolate(
    func: Callable[[Entities, World], None]
) -> Callable[[Entities, World], None]:
    """
    Used to decorate tick method of entity.

    World will run all marked method after all ticks done in a paralleled thread pool.
    Isolate tick method should NEVER interact any resource protected by a lock.
    """

    @wraps(func)
    def rtn(owner: Entities, belong: World) -> None:
        assert belong is not None, TypeError(
            "`mark_isolate` decorate must have a belong world."
        )
        belong._concurrent_tick_add(owner, cast(FutureTick, func))
        return None

    return rtn


@runtime_checkable
class Positional(Protocol):
    position: Vector


@runtime_checkable
class Movable(Positional, Protocol):
    position: Vector
    velocity: Vector
    acceleration: Vector


class Character(Entity):
    """Stand for every character, belongs to a world

    Character has position, velocity and acceleration.
    All the entity in the world is instance of character.
    """

    @staticmethod
    def check(ent: Any) -> TypeGuard[Character]:
        return isinstance(ent, Movable)

    def __init__(
        self, *, eid: int, pos: Vector, velo: Vector = Vector(0, 0, 0), **kwargs
    ) -> None:
        super().__init__(eid=eid, **kwargs)
        self.position = pos  # yes, character knows the absolute position.
        self.velocity = velo
        self.acceleration = Vector(0, 0, 0)

    def _tick(self, belong: Optional[World] = None) -> None:

        assert belong is not None, ValueError(
            "Tick method of Character must have valid belong parameter,"
            "which is a instance of World."
        )

        super()._tick(belong=belong)

    @mark_isolate
    def _position_tick(self, belong: Optional[World]) -> None:
        # Acceleration will set to 0 after a accelerate
        # if you want to continue accelerate a entity,
        # KEEP A FORCE ON IT.

        if not self.acceleration.is_zero():
            self.velocity += self.acceleration
            self.acceleration: Vector = Vector.zero()

        # Velocity will keep changing the position of a entity
        if not self.velocity.is_zero():
            self.position += self.velocity


class World(ConcurrentMixin, Entity):
    """
    The container of a set of entity.

    Entity inner the world must be Character.
    """

    def __init__(self) -> None:
        super().__init__(eid=0)
        self.entity_count = 0  # entity in total when the world created
        self.entity_dict: Dict[int, Entity] = {}  # CPython's dict is thread-safe
        self.player_dict: Dict[str, Player] = {}  # maintained by game.py.

    def __static_init__(self) -> None:
        super().__static_init__()
        self._world: Literal[None] = None
        self.__entity_count_lock = Lock()
        self.__entity_dict_lock = Lock()

    def _world_tick(self, belong: Literal[None] = None) -> None:
        for ent in self.entity_dict.values():
            ent._tick()

    @with_instance_lock("_World__entity_count_lock")
    def _world_entity_plus(self) -> int:
        """will be called whenever an entity is created"""
        self.entity_count += 1
        return self.entity_count

    # Use @with_instance_lock here will broke generic system.
    def world_new_entity(self, cls: Type[Entities], **kwargs) -> Entities:
        """
        New an entity in the world.

        **kwargs will be passed to cls to new a new entity,
        but eid is not needed, world itself will generate a correct eid as the
        first argument of cls build method.
        """

        with self.__entity_dict_lock:
            eid = self._world_entity_plus()
            new_e: Entities = cls(eid=eid, **kwargs)
            new_e._world = self  # before next tick, the _world property is set.
            self.entity_dict[eid] = new_e
            return new_e

    @with_instance_lock("_World__entity_dict_lock")
    def world_get_entity_index(self, ent: Entity) -> Optional[int]:
        for item in self.entity_dict.items():
            k, v = item
            if v == ent:
                return k
        return None

    @with_instance_lock("_World__entity_dict_lock")
    def world_get_entity(self, eid: int) -> Optional[Entity]:
        if eid in self.entity_dict.keys():
            return self.entity_dict[eid]
        else:
            return None

    @with_instance_lock("_World__entity_dict_lock")
    def world_del_entity(self, eid: int) -> None:
        if eid in self.entity_dict.keys():
            self.entity_dict.pop(eid)

    @with_instance_lock("_World__entity_dict_lock")
    def world_get_nearby_entity(
        self, target: int | Entity, radius: float
    ) -> List[Entity]:
        """
        Return character instances list near the position.

        All Positional Entity within(not include) the radius will append
        to return list.
        """

        rtn: List[Entity] = []

        valid_entity: Optional[Entity] = self.__valid_entity_input(target)
        valid_target = self.__valid_positional_input(valid_entity)
        if valid_target is None:
            return rtn

        for ent in self:
            if isinstance(ent, Positional):
                if ent != valid_target:  # Pass char itself
                    dis: float = self._get_natural_distance(ent, valid_target)
                    if dis - radius < 0:
                        rtn.append(ent)
        return rtn

    @with_instance_lock("_World__entity_dict_lock")
    def world_entity_exists(self, ent: Entity) -> bool:
        return ent in self.entity_dict.values()

    def __valid_entity_input(self, source: int | Entity) -> Optional[Entity]:
        """
        Input an int(index) or an obj,
        function will guess if the related-entity is in self, return the entity.
        else, return None.
        """

        if isinstance(source, int):

            if source not in self.entity_dict:
                return None

            return self.entity_dict[source]

        else:

            if not isinstance(source, Entity):
                return None

            if source not in self:
                return None

            return source

    @staticmethod
    def __valid_positional_input(source: Any) -> Optional[Positional]:
        if isinstance(source, Positional):
            return source
        return None

    @staticmethod
    def _get_natural_distance(target1: Positional, target2: Positional) -> float:
        p1: Vector = target1.position
        p2: Vector = target2.position
        dis: float = (p1 - p2).length()
        return dis

    @with_instance_lock("_World__entity_dict_lock")
    def world_get_natural_distance(
        self, target1: Entity | int, target2: Entity | int
    ) -> Optional[float]:
        """Return the natural distance between target1 and target2.
        Return None, if any of character provided not exists."""

        valid1, valid2 = map(self.__valid_entity_input, (target1, target2))
        valid1, valid2 = map(self.__valid_positional_input, (valid1, valid2))
        if (valid1 is None) or (valid2 is None):
            return None
        return self._get_natural_distance(valid1, valid2)

    def __iter__(self) -> Iterator[Entity]:
        return self.entity_dict.values().__iter__()


class Continuum(Thread):
    """World with time"""

    def __init__(self, world: Optional[World] = None) -> None:
        super().__init__()
        if world is None:
            world = World()
        self.world = world
        self.stop_flag = False
        self.pause_flag = False
        self.is_idle = True  # tick is not running

    def stop(self) -> None:
        """
        Set pause_flag and stop_flag to True, which will
        cause the run() method terminate.

        Then wait until the thread end.

        Cannot restart!
        """
        self.pause()
        self.stop_flag = True
        if self.is_alive():
            self.join()

    def run(self) -> None:
        """
        Main loop.
        Use `Continuum().start()` method to start the thread non-blockly.
        """

        while not self.stop_flag:  # -> STOP
            while not self.pause_flag:  # -> PAUSE
                self.is_idle = False  # -> TICK
                self.world._tick()  # -> TICK
                self.is_idle = True  # ->IDLE
        return  # -> EXIT

    def tick(self, num: int = 1) -> None:
        for i in range(num):
            self.world._tick(belong=None)

    def pause(self) -> None:
        """Wait until the game pause.
        world._world_lock would release."""
        self.pause_flag = True
        while not self.is_idle:
            pass
        return

    def resume(self) -> None:
        """Resume the game after game pause."""
        self.pause_flag = False
