import random
from typing import Optional
from math import sqrt
from collections import namedtuple


class Vector(namedtuple("Vector", ["x", "y", "z"])):
    __slots__ = ()

    @classmethod
    def zero(cls):
        """return a vector instance which is zero"""
        return Vector(0, 0, 0)

    @classmethod
    def random(cls, limit: Optional[int] = None):
        """return a random vector instance which x,y,z is in range of limit"""
        if limit:
            return Vector._make([random.randint(-limit, limit) for i in range(3)])
        else:
            return Vector._make([random.random() * 100 for i in range(3)])

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __eq__(self, other):
        return all([
            self.x == other.x,
            self.y == other.y,
            self.z == other.z
        ])

    def length(self):
        return sqrt(self.x**2 + self.y**2 + self.z**2)

    def is_zero(self) -> bool:
        return self.x == 0 and self.y == 0 and self.z == 0
