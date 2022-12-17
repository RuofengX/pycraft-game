import unittest

from threading import Lock

from pyworld.basic import Vector
from pyworld.entity import Entity
from pyworld.world import Character, Continuum, World


class TestEntity(unittest.TestCase):
    def setUp(self):
        self.ent = Entity(1)
    
    def test_properties(self):
        ent = self.ent
        assert(all((
            ent.eid == 1,
            ent.age == 0,
            isinstance(ent.uuid, int),
            not ent.report_flag,
            hasattr(ent, '_tick_lock'),
        )))
    
    def test_tick(self):
        self.ent._tick()
        assert self.ent.age == 1