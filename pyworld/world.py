from __future__ import annotations
from threading import Thread, Lock
from typing import Dict, Optional, List, TYPE_CHECKING, Type, TypeVar, Generic


from pyworld.entity import Entity
from pyworld.basic import Vector
if TYPE_CHECKING:
    from pyworld.player import Player


class Character(Entity):
    """Stand for every character, belongs to a world

    All the entity in the world is instance of character.
    """

    def __init__(
        self, eid: int, pos: Vector, velo: Vector = Vector(0, 0, 0), **kwargs
    ):
        super().__init__(eid=eid, **kwargs)
        self.position = pos
        self.velocity = velo
        self.acceleration = Vector(0, 0, 0)

    def tick(self, belong: World):  # type:ignore
        """Character has position, velocity and acceleration"""
        super().tick(belong=belong)

        # Velocity will keep changing the position of a entity
        if not self.velocity.is_zero():
            self.position += self.velocity

        # Acceleration will set to 0 after a accelerate
        # if you want to continue accelerate a entity,
        # KEEP A FORCE ON IT.
        if not self.acceleration.is_zero():
            self.velocity += self.acceleration
            self.acceleration = Vector.zero()


Characters = TypeVar("Characters", bound=Character)


class World(Generic[Characters], Entity):
    """The container of a set of beings"""

    def __init__(self) -> None:
        super().__init__(eid=0)
        self.entity_count = 0  # entity in total when the world created
        self.entity_dict: Dict[int, Character] = {}
        self.player_dict: Dict[str, Player] = {}  # HACK: here Character is Player.

    def __static_init__(self):
        super().__static_init__()
        self.__entity_count_lock = Lock()

    def tick(self, belong=None) -> None:
        super().tick(belong=belong)
        for ent in self.entity_dict.values():
            ent.tick(belong=self)

    def world_entity_plus(self) -> int:
        """will be called whenever a entity is created"""
        with self.__entity_count_lock:
            self.entity_count += 1
        return self.entity_count

    def world_new_character(self, pos: Vector) -> Character:
        eid = self.world_entity_plus()
        new_c = Character(eid=eid, pos=pos)
        self.entity_dict[eid] = new_c
        return new_c

    def world_new_entity(
        self, cls: Type[Characters], **kwargs
    ) -> Characters:
        # HACK: Use generic to regulate the type of arg 'cls'
        """New an entity in the world. If cls is given, use cls as the generator.
        *args and **kwargs will be passed to cls to new a new entity,
        but eid is not needed, world itself will generate a correct eid as the
        first argument of cls."""
        eid = self.world_entity_plus()
        new_e = cls(eid=eid, **kwargs)
        self.entity_dict[eid] = new_e
        return new_e

    def world_del_entity(self, eid: int) -> None:
        if eid in self.entity_dict.keys():
            self.entity_dict.pop(eid)

    def world_get_entity(self, eid: int) -> Optional[Character]:
        if eid in self.entity_dict.keys():
            return self.entity_dict[eid]
        else:
            return None

    def world_get_nearby_character(
        self, char: Character, radius: float
    ) -> List[Character]:
        """Return character instances list nearby the position"""
        rtn = []

        for ent in self.entity_dict.values():
            if ent != char:  # Pass char itself
                dis = self.world_get_lineral_distance(char, ent)
                if dis is not None:
                    if dis - radius < 0:
                        rtn.append(ent)
        return rtn

    def world_get_character_index(self, ent: Character) -> Optional[int]:
        for item in self.entity_dict.items():
            k, v = item
            if v == ent:
                return k
        return None

    def world_character_exists(self, ent: Character) -> bool:
        return ent in self.entity_dict

    def world_natural_distance(
        self, target1: Character | int, target2: Character | int
    ) -> Optional[float]:
        """Return the natural distance between char1 and char2.
        Return None, if any of character provided not exists."""

        ent_list = self.entity_dict.values()

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

        if char1 in ent_list and char2 in ent_list:
            p1 = char1.position
            p2 = char2.position
            dis = (p1 - p2).length()
            return dis

        return None

    def world_get_lineral_distance(
        self, target1: Character | int, target2: Character | int
    ) -> Optional[float]:
        """Return the distance but in sum(delta x, y, z) like,
        (I call it lineral distance)
        Return None, if any of character provided not exists."""
        ent_list = self.entity_dict.values()

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

        if char1 in ent_list and char2 in ent_list:
            p1 = char1.position
            p2 = char2.position
            dis = abs(p1.x - p2.x) + (p1.y - p2.y) + (p1.z - p2.z)
            return dis

        return None


class Continuum(Thread):
    """World with time"""

    def __init__(self, world: Optional[World] = None):
        super().__init__()
        if world is None:
            world = World()
        self.world = world
        self.__world_lock = Lock()
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
        self.pause_flag = True
        self.stop_flag = True
        if self.is_alive():
            self.join()

    def run(self):
        """Thread run the loop.

        Use `.start()` method instead.
        """
        while not self.stop_flag:
            while not self.pause_flag:
                self.is_idle = False
                with self.__world_lock:
                    self.world.tick()
                self.is_idle = True

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
