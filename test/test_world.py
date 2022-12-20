import unittest

from pyworld.basic import Vector
from pyworld.entity import Entity
from pyworld.world import Character, Continuum, World


class TestEntity(Entity):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._test_target: bool = False

    def _test_tick(self, belong: World) -> None:
        self._test_target = True


class TestWorld(unittest.TestCase):
    def setUp(self) -> None:
        self.ct: Continuum = Continuum()
        self.test_ent: TestEntity = self.ct.world.world_new_entity(cls=TestEntity)

        self.char1: Character = self.ct.world.world_new_entity(
            Character, pos=Vector(0, 0, 0)
        )
        self.char2: Character = self.ct.world.world_new_entity(
            Character, pos=Vector(0, 1, 0)
        )
        self.char3: Character = self.ct.world.world_new_entity(
            Character, pos=Vector(0, 10, 0)
        )
        self.char4: Character = self.ct.world.world_new_entity(
            Character, pos=Vector(0, -10, 0)
        )
        self.char5: Character = self.ct.world.world_new_entity(
            Character, pos=Vector(0, 11, 0)
        )

    def tearDown(self) -> None:
        del self.ct

    def test_world_tick(self) -> None:
        self.ct.world._tick()
        assert self.ct.world.age == 1
        assert self.test_ent._test_target

    def test_entity_plus(self) -> None:
        assert self.ct.world.entity_count == 6
        self.ct.world.world_new_entity(Character, pos=Vector(1, 0, 1))
        assert self.ct.world.entity_count == 7

    def test_new_character(self) -> None:
        assert self.test_ent is self.ct.world.entity_dict[1]
        assert self.test_ent._world == self.ct.world

    def test_world_property(self) -> None:
        assert self.test_ent._world == self.ct.world
        self.test_ent._world = None
        self.ct.world._tick()
        assert self.test_ent._world == self.ct.world

    def test_iter(self) -> None:
        ent_list = [
            self.test_ent,
            self.char1,
            self.char2,
            self.char3,
            self.char4,
            self.char5,
        ]
        for i in self.ct.world:
            assert i in ent_list

    def test_in(self) -> None:
        ent_list = [
            self.test_ent,
            self.char1,
            self.char2,
            self.char3,
            self.char4,
            self.char5,
        ]
        for i in ent_list:
            assert i in self.ct.world
        assert Entity() not in self.ct.world

    def test_get_entity_index(self) -> None:
        assert self.ct.world.world_get_entity_index(self.test_ent) == 1

    def test_get_entity(self) -> None:
        assert self.ct.world.world_get_entity(1) is self.test_ent

    def test_del_entity(self) -> None:
        for i in range(1, 7):
            self.ct.world.world_del_entity(i)
        assert self.ct.world.entity_dict == {}

    def test_get_nearby_entity(self) -> None:

        assert (
            self.ct.world.world_get_nearby_entity(
                self.char1,
                radius=1.0,
            )
            == []
        )
        assert self.ct.world.world_get_nearby_entity(
            self.char1,
            radius=1.1,
        ) == [self.char2]
        assert self.ct.world.world_get_nearby_entity(
            self.char3,
            radius=1.1,
        ) == [self.char5]
        for char in [self.char1, self.char2, self.char3, self.char4, self.char5]:
            target = {
                self.char1,
                self.char2,
                self.char3,
                self.char4,
                self.char5,
            }
            target.remove(char)

            assert (
                set(
                    self.ct.world.world_get_nearby_entity(
                        char,
                        radius=50,
                    )
                )
                == target
            )

    def test_entity_exists(self) -> None:
        not_in_world_ent = Character(eid=1, pos=Vector.random())
        assert not self.ct.world.world_entity_exists(not_in_world_ent)
        assert self.ct.world.world_entity_exists(self.test_ent)
        assert self.ct.world.world_entity_exists(self.char1)

    def test_get_natural_distance(self) -> None:
        assert (
            self.ct.world.world_get_natural_distance(
                self.char1, Character(eid=0, pos=Vector(0, 0, 0))
            )
            is None
        )
        assert self.ct.world.world_get_natural_distance(self.char1, self.char2) == 1
        char6 = self.ct.world.world_new_entity(Character, pos=Vector(3, 4, 0))
        char7 = self.ct.world.world_new_entity(Character, pos=Vector(12, 0, 5))
        assert self.ct.world.world_get_natural_distance(self.char1, char6) == 5
        assert self.ct.world.world_get_natural_distance(self.char1, char7) == 13


class TestCharacter(unittest.TestCase):
    def setUp(self) -> None:
        self.ct = Continuum()
        return super().setUp()

    def tearDown(self) -> None:
        del self.ct
        return super().tearDown()

    def test_character_move(self) -> None:
        c_move: Character = self.ct.world.world_new_entity(
            cls=Character, pos=Vector(0, 0, 0), velo=Vector(0, 0, 1)
        )
        self.ct.world._tick()
        assert c_move.position == Vector(0, 0, 1)
