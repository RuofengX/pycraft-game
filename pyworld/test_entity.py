from __future__ import annotations

import time
import unittest

from objprint import op  # type: ignore

from pyworld.basic import Vector
from pyworld.world import Character, World, tick_isolate


class IsolateEntity(Character):

    @tick_isolate
    def isolate_test_tick(self, belong: World | None) -> None:
        time.sleep(1)
        print(self.age)


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

    def test_iso_tick(self):
        for i in range(3):
            self.world._tick()
        op(self.world.entity_dict)


if __name__ == '__main__':
    unittest.main()
