import unittest
from dataclasses import dataclass

from pyworld.world import Continuum, Character
from pyworld.entity import Entity
from pyworld.basic import Vector


@dataclass
class TestEntity(Entity):
    _test_target: bool = False

    def _test_tick(self):
        self._test_target = True


class TestWorld(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()

        self.test_ent = self.ct.world.world_new_entity(cls=TestEntity)

    def test_mixin_tick(self):
        self.ct.world._tick()
        assert self.test_ent._test_target

    def test_character_move(self):
        c_move = self.ct.world.world_new_entity(
            cls=Character, pos=Vector(0, 0, 0), velo=Vector(0, 0, 1)
        )
        self.ct.world._tick()
        assert c_move.position == Vector(0, 0, 1)
