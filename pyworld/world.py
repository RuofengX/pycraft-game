from __future__ import annotations
from math import sqrt
from collections import namedtuple
from threading import Thread, Lock
from typing import Dict, Optional, List, TypeVar, Type

from objprint import op  # type: ignore


class Entity:
    """Being

    An entity of a world should only be created by World.create_entity() method.
    Because an eid should be taken to create an entity.
    """

    def __init__(self, eid: int):
        super().__init__()
        self.__static_init__()
        self.eid = eid
        self.age = 0
        self.report_flag = False

    def __static_init__(self):
        """Will be called when loading from pickle bytes."""
        pass

    def tick(self, belong: Entity = None):
        """Describe what a entity should do in a tick."""
        self.age += 1
        if self.report_flag:
            self.report()

        # Call every function named after _tick of class
        for func in dir(
            self
        ):  # dir() could show all instance (include father's) method
            if func[-5:] == "_tick":
                getattr(self, func)(belong=belong)

    def report(self):
        """Report self, for logging or debuging usage."""
        if self.age % 20 == 0:
            print('-' * 10)
            op(self.__dict__)

    def __getstate__(self) -> dict:
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


class Vector(namedtuple("Vector", ["x", "y", "z"])):
    __slots__ = ()

    @classmethod
    def zero(cls):
        """return a vector instance which is zero"""
        return Vector(0, 0, 0)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def length(self):
        return sqrt(self.x**2 + self.y**2 + self.z**2)

    def is_zero(self) -> bool:
        return self.x == 0 and self.y == 0 and self.z == 0


class Character(Entity):
    """Stand for every character, belongs to a world

    All the entity in the world is instance of character.
    """

    def __init__(self, eid: int, pos: Vector, velo: Vector = Vector(0, 0, 0)):
        super().__init__(eid=eid)
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


class World(Entity):
    """The container of a set of beings"""

    def __init__(self) -> None:
        super().__init__(eid=0)
        self.entity_count = 0  # entity in total when the world created
        self.entity_dict: Dict[int, Character] = {}

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

    def world_new_entity(self, cls=Character, *args, **kargs):
        # TODO: Use generic to regulate the type of arg 'cls'
        """New an entity in the world. If cls is given, use cls as the generator."""
        eid = self.world_entity_plus()
        new_e = cls(eid, *args, **kargs)
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
