from __future__ import annotations
from collections import namedtuple
from threading import Thread, Lock
from typing import Dict

from pprint import pprint
from objprint import op  # type:ignore


class Entity:
    """Being"""

    def __init__(self, eid: int):
        super().__init__()
        self.eid = eid
        self._report_flag = False

    def tick(self, belong: Entity):
        """Describe what a entity should do in a tick."""
        raise NotImplementedError

    def report(self):
        """Report self, for logging or debuging useage."""
        op(self)


class Vector(namedtuple("Vector", ["x", "y", "z"])):
    __slots__ = ()

    @classmethod
    def zero(cls):
        """return a vector instance which is_zero"""
        return Vector(0, 0, 0)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.y, self.x - other.y, self.z - other.z)

    def is_zero(self) -> bool:
        return self.x == 0 and self.y == 0 and self.z == 0


class Charactor(Entity):
    """Stand for every charactor, belongs to a world"""

    def __init__(self, eid: int, pos: Vector, velo: Vector = Vector(0, 0, 0)):
        super().__init__(eid=eid)
        self.position = pos
        self.velocity = velo
        self.acceleration = Vector(0, 0, 0)

    def report(self):
        pprint({
            'name': self.__class__.__name__,
            'positon': self.position,
            'velocity': self.velocity,
            'acceleration': self.acceleration
        })

    def tick(self, belong: World):  # type:ignore
        """Character has position, velocity and acceleration"""

        # Velocity will keep changing the position of a entity
        if not self.velocity.is_zero():
            self.position += self.velocity

        # Acceleration will set to 0 after a accelerate
        # if you want to continue accelerate a entity,
        # KEEP A FORCE ON IT.
        if not self.acceleration.is_zero():
            self.velocity += self.acceleration
            self.acceleration = Vector.zero()

        # Report self if needed.
        if self._report_flag:
            self.report()


class World(Entity):
    """The container of a set of beings"""

    def __init__(self):
        super().__init__(eid=0)
        self.entity_count = 0  # entity in total when the world created
        self._entity_count_lock = Lock()
        self.entity_dict: Dict[int, Entity] = {}

    def _entity_count_plus(self):
        """will be called whenever a entity is created"""
        with self._entity_count_lock:
            self.entity_count += 1
        return self.entity_count

    def tick(self, belong: Continuum):  # type:ignore
        for ent in self.entity_dict.values():
            ent.tick(belong=self)

    def new_character(self, pos: Vector):
        eid = self._entity_count_plus()
        new_c = Charactor(eid=eid, pos=pos)
        self.entity_dict[eid] = new_c
        return new_c

    def _new_ent(self):
        eid = self._entity_count_plus()
        new_e = Entity(eid=eid)
        self.entity_dict[eid] = new_e

    def _del_ent(self, eid: int):
        self.entity_dict.pop(eid)


class Continuum(World, Thread):
    """World with time"""
    def __init__(self):
        super().__init__()
        self._world_lock = Lock()
        self.age = 0
        self.stop_flag = False

        # self.start()

    def report(self):
        pprint({
            "age": self.age,
            "entity_alive": len(self.entity_dict),
            "entity_total": self.entity_count
        })

    def stop(self):
        self.stop_flag = True

    def run(self):
        while not self.stop_flag:
            self.age += 1
            with self._world_lock:
                self.tick(belong=self)
            self.report()
