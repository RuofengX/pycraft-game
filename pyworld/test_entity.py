from __future__ import annotations
import unittest
import time

from objprint import op  # type: ignore

from pyworld.world import World, Character, tick_isolate
from pyworld.basic import Vector


class IsolateEntity(Character):

    @tick_isolate
    def isolate_test_tick(self, belong: World | None) -> None:
        time.sleep(1)
        print(1)


class TestEntity(unittest.TestCase):

    def setUp(self):
        self.world = World()
        self.ent = self.world.world_new_entity(cls=IsolateEntity, pos=Vector(0, 0, 0))
        for i in range(10):
            self.world.world_new_entity(
                cls=IsolateEntity,
                pos=Vector(0, 0, 0),
                velo=Vector(1, 0, 0)
            )

    def tearDown(self):
        pass

    @unittest.skip('Passed')
    def test_iso_tick(self):
        for i in range(3):
            self.world.tick()
        op(self.world.entity_dict)


if __name__ == '__main__':
    unittest.main()
