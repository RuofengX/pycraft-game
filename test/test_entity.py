import pickle
from typing import Optional

import unittest

from pyworld.entity import Entity


class TEntity(Entity):
    def __init__(self, eid: int = -1):
        super().__init__(eid)
        self.tick_times = 0
        self.tick_last_time = 0

    def _tick(self, belong: Optional[Entity] = None) -> None:
        self.tick_times += 1
        return super()._tick(belong)

    def _tick_last(self, belong: Optional[Entity] = None) -> None:
        self.tick_last_time += 1
        return super()._tick_last(belong)


class TestEntity(unittest.TestCase):
    def setUp(self):
        self.ent = Entity(1)
        self.t_entity = TEntity(2)

    def test_properties(self):
        ent = self.ent
        assert all(
            (
                ent.eid == 1,
                ent.age == 0,
                isinstance(ent.uuid, int),
                not ent.report_flag,
                hasattr(ent, "_tick_lock"),
            )
        )

    def test_tick(self):
        self.ent._tick()
        self.t_entity._tick()
        assert self.ent.age == 1
        assert self.t_entity.age == 1
        for i in range(10):
            self.t_entity._tick()
        assert self.t_entity.tick_times == 11

    def test_tick_last(self):
        self.t_entity._tick()
        assert self.t_entity.tick_last_time == 1

class TestPickleSystem(TestEntity):
    def setUp(self):
        super().setUp()
        pickle_b = pickle.dumps(self.ent)
        self.ent = pickle.loads(pickle_b)
        
    

        # TODO