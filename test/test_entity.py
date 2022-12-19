import pickle
from threading import Lock
from typing import Optional

import unittest

from pyworld.entity import Entity, with_instance_lock


class TEntity(Entity):
    def __init__(self) -> None:
        super().__init__(eid=-1)
        self.tick_times = 0
        self.tick_last_time = 0

    def _tick(self, belong: Optional[Entity] = None) -> None:
        self.tick_times += 1
        return super()._tick(belong)

    def _tick_last(self, belong: Optional[Entity] = None) -> None:
        self.tick_last_time += 1
        return super()._tick_last(belong)


class TestLockDeco(unittest.TestCase):
    class DecoTestEntity(Entity):
        def __static_init__(self) -> None:
            self._lock = Lock()
            return super().__static_init__()

        @with_instance_lock("_lock", debug=True)
        def do_atom(self, t: int) -> int:
            assert self._lock.locked()
            return t

    class NoLockEntity(Entity):
        @with_instance_lock("_lock", debug=True)
        def do_atom(self, t: int) -> int:
            return t

    def test_deco(self) -> None:
        t_ent = self.DecoTestEntity()
        assert t_ent.do_atom(1) == 1
        assert t_ent.do_atom(1) == 1
        assert t_ent.do_atom(1) == 1
    
    def test_no_deco(self) -> None:
        t_ent = self.NoLockEntity()
        pass_flag = False
        try:
            t_ent.do_atom(1)
        except AttributeError:
            pass_flag = True
        finally:
            assert pass_flag



class TestEntity(unittest.TestCase):
    def setUp(self) -> None:
        self.ent = Entity()
        self.t_entity = TEntity()

    def test_properties(self) -> None:
        ent = self.ent
        assert all(
            (
                ent.eid == -1,
                ent.age == 0,
                isinstance(ent.uuid, int),
                not ent.report_flag,
                hasattr(ent, "_tick_lock"),
            )
        )

    def test_tick(self) -> None:
        self.ent._tick()
        self.t_entity._tick()
        assert self.ent.age == 1
        assert self.t_entity.age == 1
        for i in range(10):
            self.t_entity._tick()
        assert self.t_entity.tick_times == 11

    def test_tick_last(self) -> None:
        self.t_entity._tick()
        assert self.t_entity.tick_last_time == 1

class TestPickleSystem(TestEntity):
    def setUp(self) -> None:
        super().setUp()
        pickle_b = pickle.dumps(self.ent)
        self.ent = pickle.loads(pickle_b)
        # TODO
