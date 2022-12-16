import unittest

from pyworld.basic import Vector
from pyworld.entity import Entity
from pyworld.world import Character, Continuum, World


class TestEntity(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._test_target: bool = False

    def _test_tick(self, belong: World) -> None:
        self._test_target = True


class TestWorld(unittest.TestCase):
    def setUp(self) -> None:
        self.ct: Continuum = Continuum()

        self.test_ent: TestEntity = self.ct.world.world_new_entity(cls=TestEntity)

    def test_mixin_tick(self) -> None:
        self.ct.world._tick()
        assert self.test_ent._test_target

    def test_character_move(self) -> None:
        c_move: Character = self.ct.world.world_new_entity(
            cls=Character, pos=Vector(0, 0, 0), velo=Vector(0, 0, 1)
        )
        self.ct.world._tick()
        assert c_move.position == Vector(0, 0, 1)
    


if __name__ == "__main__":
    unittest.main()
