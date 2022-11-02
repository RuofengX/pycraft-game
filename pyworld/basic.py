from __future__ import annotations
import random
from typing import Optional, final, Any
import operator
import itertools

import numpy as np


@final
class Vector():

    __slots__ = ['x', 'y', 'z', 'raw_array']  # FIXME slots cannot be pickled

    @classmethod
    def zero(cls):
        """return a vector instance which is zero"""
        return Vector(0, 0, 0)

    @classmethod
    def random(cls, limit: Optional[int] = None):
        """return a random vector instance which x,y,z is in range of limit"""
        if limit:
            return Vector(*(random.randint(-limit, limit) for i in range(3)))
        else:
            return Vector(*(random.random() * 100 for i in range(3)))

    @classmethod
    def from_ndarray(cls, ndarray: np.ndarray) -> Vector:
        x, y, z, *_ = ndarray[:, 0]
        rtn = Vector(x, y, z, update_array=False)
        rtn.raw_array = ndarray
        return rtn

    @staticmethod
    def dotproduct(vec1: Vector, vec2: Vector) -> float:
        return np.vdot(vec1.raw_array, vec2.raw_array)

    def __init__(self, x: float, y: float, z: float, update_array=True):
        """Use x, y, z to create a 3-D vector.
        Update inner property raw_array if update_array is True
        Otherwise you should set the raw_array property afterwards."""
        self.x = x
        self.y = y
        self.z = z
        if update_array:
            self._updata_array()

    def _updata_array(self):
        """Manually update inner array.
        Row vector is used in pyworld."""
        self.raw_array = np.array([
            [self.x],
            [self.y],
            [self.z],
        ])

    def length(self) -> np.floating[Any]:
        return np.linalg.norm(self.raw_array)

    def is_zero(self) -> bool:
        return all(map(operator.eq, self, itertools.repeat(0)))

    def unit(self) -> Vector:
        if self.length() == 0:
            raise ValueError("Zero vector doesn't have direct")
        raw = self.raw_array
        unit_array = raw / np.full_like(raw, self.length())
        return Vector.from_ndarray(unit_array)

    def __array__(self) -> np.ndarray:
        return self.raw_array

    def __add__(self, other):
        if not isinstance(other, Vector):
            raise TypeError(f'Unsupport type {other.__class__}')
        return Vector.from_ndarray(self.raw_array + other.raw_array)

    def __sub__(self, other):
        if not isinstance(other, Vector):
            raise TypeError(f'Unsupport type {other.__class__}')
        return Vector.from_ndarray(self.raw_array - other.raw_array)

    def __mul__(self, num: float):
        return Vector.from_ndarray(num * self.raw_array)

    def __div__(self, num: float):
        return Vector.from_ndarray(self.raw_array / num)

    def __iter__(self):
        return (self.x, self.y, self.z).__iter__()

    def __eq__(self, other):
        if isinstance(other, Vector):
            return all(map(operator.eq, self, other))
        else:
            return False

    def __repr__(self):
        return str((self.x, self.y, self.z))

    def __getstate__(self):
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
        }

    def __setstate__(self, state):
        self.x = state['x']
        self.y = state['y']
        self.z = state['z']
        self._updata_array()

    @property
    def __dict__(self):
        return self.__getstate__()
