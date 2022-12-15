from __future__ import annotations

import time
from functools import wraps
from threading import Lock, Thread
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
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
from pyworld.entity import Checkable, ConcurrentMixin, Entities, Entity, FutureTick

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
class Movable(Protocol):
    position: Vector
    velocity: Vector
    acceleration: Vector


class Character(Checkable, Entity):
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
        self.__entity_count_lock = Lock()

    def _world_tick(self, belong: Literal[None] = None) -> None:
        time.sleep(0.1)
        for ent in self.entity_dict.values():
            ent._tick(belong=self)

    def _world_entity_plus(self) -> int:
        """will be called whenever an entity is created"""
        with self.__entity_count_lock:
            self.entity_count += 1
        return self.entity_count

    def world_new_entity(self, cls: Type[Entities], **kwargs) -> Entities:
        """
        New an entity in the world.

        **kwargs will be passed to cls to new a new entity,
        but eid is not needed, world itself will generate a correct eid as the
        first argument of cls build method.
        """

        eid = self._world_entity_plus()
        new_e: Entities = cls(eid=eid, **kwargs)
        self.entity_dict[eid] = new_e
        return new_e

    def world_del_entity(self, eid: int) -> None:
        if eid in self.entity_dict.keys():
            self.entity_dict.pop(eid)

    def world_get_entity(self, eid: int) -> Optional[Entity]:
        if eid in self.entity_dict.keys():
            return self.entity_dict[eid]
        else:
            return None

    def world_get_nearby_entity(
        self, char: Character, radius: float
    ) -> List[Character]:
        """Return character instances list near the position"""
        rtn: List[Character] = []

        for ent in self.entity_dict.values():
            if Character.check(ent):
                if ent != char:  # Pass char itself
                    dis: float | None = self.world_get_natural_distance(char, ent)
                    if dis is not None:
                        if dis - radius < 0:
                            rtn.append(ent)
        return rtn

    def world_get_entity_index(self, ent: Entity) -> Optional[int]:
        for item in self.entity_dict.items():
            k, v = item
            if v == ent:
                return k
        return None

    def world_entity_exists(self, ent: Entity) -> bool:
        return ent in self.entity_dict

    def world_get_natural_distance(
        self, target1: Character | int, target2: Character | int
    ) -> Optional[float]:
        """Return the natural distance between char1 and char2.
        Return None, if any of character provided not exists."""

        if isinstance(target1, int):
            char1: Optional[Entity] = self.world_get_entity(target1)
        else:
            char1 = target1

        if isinstance(target2, int):
            char2: Optional[Entity] = self.world_get_entity(target2)
        else:
            char2 = target2

        if char1 is None or char2 is None:
            return None

        if Character.check(char1) and Character.check(char2):
            p1: Vector = char1.position
            p2: Vector = char2.position
            dis: float = (p1 - p2).length()
            return dis

        return None

    def world_get_lineal_distance(
        self, target1: Character | int, target2: Character | int
    ) -> Optional[float]:
        """Return the distance but in sum(delta x, y, z) like,
        (I call it lineal distance)
        Return None, if any of character provided not exists."""

        if isinstance(target1, int):
            char1 = self.world_get_entity(target1)
        else:
            char1 = target1

        if isinstance(target2, int):
            char2 = self.world_get_entity(target2)
        else:
            char2 = target2

        if not (char1 and char2):
            return None

        if Character.check(char1) and Character.check(char2):
            p1 = char1.position
            p2 = char2.position
            dis = abs(p1.x - p2.x) + abs(p1.y - p2.y) + abs(p1.z - p2.z)
            return dis

        return None


class Continuum(Thread):
    """World with time"""

    def __init__(self, world: Optional[World] = None):
        super().__init__()
        if world is None:
            world = World()
        self.world = world
        self.stop_flag = False
        self.pause_flag = False
        self.is_idle = True  # tick is not running

    def stop(self):
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

    def run(self):
        """Thread run the loop.

        Use `.start()` method instead.
        """

        while not self.stop_flag:  # -> STOP
            while not self.pause_flag:  # -> PAUSE
                self.is_idle = False  # -> TICK
                self.world._tick()  # -> TICK
                self.is_idle = True  # ->IDLE
        return  # -> EXIT

    def pause(self):
        """Wait until the game pause.
        world._world_lock would release."""
        self.pause_flag = True
        while not self.is_idle:
            pass
        return

    def resume(self):
        """Resume the game after game pause."""
        self.pause_flag = False
