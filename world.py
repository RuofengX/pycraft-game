from __future__ import annotations
from math import sqrt
from collections import namedtuple
from threading import Thread, Lock
from typing import Dict, Optional, List

from pprint import pprint
from objprint import op  # type:ignore


class Entity:
    """Being"""

    def __init__(self, eid: int):
        super().__init__()
        self.eid = eid
        self.age = 0
        self._report_flag = False

    def tick(self, belong: Entity = None):
        """Describe what a entity should do in a tick."""
        self.age += 1
        if self._report_flag:
            self.report()

    def report(self):
        """Report self, for logging or debuging useage."""
        op(self)


class Vector(namedtuple("Vector", ["x", "y", "z"])):
    __slots__ = ()

    @classmethod
    def zero(cls):
        """return a vector instance which is zero"""
        return Vector(0, 0, 0)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.y, self.x - other.y, self.z - other.z)

    def length(self):
        return sqrt(self.x**2 + self.y**2 + self.z**2)

    def is_zero(self) -> bool:
        return self.x == 0 and self.y == 0 and self.z == 0


class Character(Entity):
    """Stand for every character, belongs to a world"""

    def __init__(self, eid: int, pos: Vector, velo: Vector = Vector(0, 0, 0)):
        super().__init__(eid=eid)
        self.position = pos
        self.velocity = velo
        self.acceleration = Vector(0, 0, 0)

    def report(self):
        pprint(
            {
                "type": self.__class__.__name__,
                "positon": self.position,
                "velocity": self.velocity,
                "acceleration": self.acceleration,
            }
        )

    def tick(self, belong: World):  # type:ignore
        """Character has position, velocity and acceleration"""
        super().tick()

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

    def __init__(self):
        super().__init__(eid=0)
        self.entity_count = 0  # entity in total when the world created
        self._entity_count_lock = Lock()
        self.entity_dict: Dict[int, Character] = {}

    def _entity_count_plus(self):
        """will be called whenever a entity is created"""
        with self._entity_count_lock:
            self.entity_count += 1
        return self.entity_count

    def tick(self, belong=None):
        super().tick()
        for ent in self.entity_dict.values():
            ent.tick(belong=self)

    def new_character(self, pos: Vector):
        eid = self._entity_count_plus()
        new_c = Character(eid=eid, pos=pos)
        self.entity_dict[eid] = new_c
        return new_c

    def del_character(self, eid: int):
        if eid in self.entity_dict.keys():
            self.entity_dict.pop(eid)

    def get_entity(self, eid: int) -> Optional[Entity]:
        if eid in self.entity_dict.keys():
            return self.entity_dict[eid]
        else:
            return None

    def get_character_nearby(
        self, char: Character, radius: float
    ) -> List[Character]:
        """Return character instances list nearby the position"""
        rtn = []

        for ent in self.entity_dict.values():
            if ent != char:  # Pass char itself
                dis = self._get_lineral_distance(char, ent)
                if dis is not None:
                    if dis - radius < 0:
                        rtn.append(ent)
        return rtn

    def _get_natural_distance(
        self, char1: Character, char2: Character
    ) -> Optional[float]:
        """Return the natural distance between char1 and char2.
        Return None, if any of character provided not exists."""
        ent_list = self.entity_dict.values()

        if char1 in ent_list and char2 in ent_list:
            p1 = char1.position
            p2 = char2.position
            dis = (p1 - p2).length()
            return dis

        return None

    def _get_lineral_distance(
        self, char1: Character, char2: Character
    ) -> Optional[float]:
        """Return the distance but in sum(delta x, y, z) like,
        (I call it lineral distance)
        Return None, if any of character provided not exists."""
        ent_list = self.entity_dict.values()

        if char1 in ent_list and char2 in ent_list:
            p1 = char1.position
            p2 = char2.position
            dis = abs(p1.x - p2.x) + (p1.y - p2.y) + (p1.z - p2.z)
            return dis
        return None


class Continuum(World, Thread):
    """World with time"""

    def __init__(self):
        super().__init__()
        self._world_lock = Lock()
        self.stop_flag = False

        # self.start()

    def report(self):
        pprint(
            {
                "age": self.age,
                "entity_alive": len(self.entity_dict),
                "entity_total": self.entity_count,
            }
        )

    def stop(self):
        self.stop_flag = True

    def run(self):
        while not self.stop_flag:
            with self._world_lock:
                self.tick()
