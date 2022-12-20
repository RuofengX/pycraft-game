import unittest

from pyworld.basic import Vector
from pyworld.entity import Entity
from pyworld.modules.equipment import Equipment, EquipmentMixin
from pyworld.modules.equipments.radar import Radar
from pyworld.world import Character, Continuum


class EquipMixinEntity(EquipmentMixin, Entity):
    pass


class NotExist:
    pass


class TestModule(Equipment):
    require_module = EquipMixinEntity
    limit_num = 3


class TestReqModule(Equipment):
    require_module = NotExist


class TestLimitModule(Equipment):
    limit_num = 0


class TestEquipBase(unittest.TestCase):
    def setUp(self) -> None:
        self.ct = Continuum()
        self.ent = self.ct.world.world_new_entity(EquipMixinEntity)

    def test_ensure_feature(self) -> None:
        assert not self.ent._equip_add(TestReqModule())
        assert not self.ent._equip_add(TestLimitModule())
        assert self.ent.equip_list == []

    def test_equip_on(self) -> None:
        eqp = TestModule()
        assert self.ent._equip_add(eqp)
        assert self.ent.equip_list == [eqp]

        ent2 = EquipMixinEntity()
        assert not ent2._equip_add(eqp)
        assert self.ent._equip_pop(eqp) == eqp
        assert ent2._equip_add(eqp)

    def test_limit(self) -> None:
        assert self.ent._equip_available(TestModule) == TestModule.limit_num
        eqp0 = TestModule()
        eqp1 = TestModule()
        eqp2 = TestModule()
        eqp3 = TestModule()
        assert self.ent._equip_add(eqp0)
        assert self.ent._equip_available(TestModule) == TestModule.limit_num - 1
        assert self.ent._equip_add(eqp1)
        assert self.ent._equip_available(TestModule) == TestModule.limit_num - 2
        assert self.ent._equip_add(eqp2)
        assert self.ent._equip_available(TestModule) == TestModule.limit_num - 3
        assert not self.ent._equip_add(eqp3)
        assert self.ent._equip_available(TestModule) == TestModule.limit_num - 3

    def test_pop(self) -> None:
        eqp = TestModule()
        assert self.ent._equip_add(eqp)
        assert self.ent._equip_pop("TestModule") == eqp
        assert self.ent.equip_list == []

    def test_get(self) -> None:
        eqp = TestModule()
        eqp_2 = TestModule()
        eqp_3 = TestModule()
        assert self.ent._equip_add(eqp)
        assert self.ent._equip_add(eqp_2)
        assert self.ent._equip_add(eqp_3)

        assert self.ent._equip_get(TestModule) == eqp
        assert self.ent._equip_get("TestModule") == eqp

        assert self.ent._equip_get(TestModule, 1) == eqp_2
        assert self.ent._equip_get("TestModule", 1) == eqp_2

        assert self.ent._equip_get(TestModule, 2) == eqp_3
        assert self.ent._equip_get("TestModule", 2) == eqp_3


class TestRadar(unittest.TestCase):
    class NoPosition(EquipmentMixin, Entity):
        pass

    class Position(EquipmentMixin, Character):
        pass

    def setUp(self) -> None:
        self.ct = Continuum()
        self.radar = self.ct.world.world_new_entity(Radar)
        self.no_position = self.ct.world.world_new_entity(cls=self.NoPosition)
        self.position = self.ct.world.world_new_entity(
            cls=self.Position, pos=Vector(0, 0, 0)
        )
        self.position0 = self.ct.world.world_new_entity(
            cls=self.Position, pos=Vector(0, 0, 0)
        )
        self.position1 = self.ct.world.world_new_entity(
            cls=self.Position, pos=Vector(0, 0, 1)
        )
        self.position2 = self.ct.world.world_new_entity(
            cls=self.Position, pos=Vector(0, 0, 2)
        )
        self.position3 = self.ct.world.world_new_entity(
            cls=self.Position, pos=Vector(0, 0, 3)
        )
        self.moving0 = self.ct.world.world_new_entity(
            cls=Character, pos=Vector(3, 0, 0), velo=Vector(-1, 0, 0)
        )

    def test_require(self) -> None:
        assert not self.no_position._equip_add(self.radar)
        assert self.position._equip_add(self.radar)
        assert self.position.equip_list == [self.radar]

    def test_limit(self) -> None:
        assert self.position._equip_add(self.radar)
        assert self.position.equip_list == [self.radar]
        assert not self.position._equip_add(self.radar)
        assert self.position.equip_list == [self.radar]

    def test_scan(self) -> None:
        assert self.position._equip_add(self.radar)
        assert self.position.equip_list == [self.radar]
        self.radar.set_scan_frequence(1)
        self.radar.radius = 0
        self.ct.world._tick()
        assert self.radar.scan_result == []

        self.radar.radius = 0.1
        self.radar._radar_tick(self.ct.world)
        assert self.radar.scan_result == [self.position0]

        self.radar.radius = 1.1
        self.radar._radar_tick(self.ct.world)
        assert self.radar.scan_result == [self.position0, self.position1]

        self.radar.radius = 2.1
        assert self.ct.world.world_del_entity(
            self.ct.world.world_get_entity_index(self.moving0)
        ) == self.moving0
        self.radar._radar_tick(self.ct.world)
        assert self.radar.scan_result == [
            self.position0,
            self.position1,
            self.position2,
        ]

    def test_scan_moving(self) -> None:
        assert self.position._equip_add(self.radar)
        assert self.position.equip_list == [self.radar]
        self.radar.radius = 1.1
        self.radar.set_scan_frequence(1)
        self.ct.tick(2)
        assert self.moving0 not in self.radar.scan_result
        self.ct.tick(2)
        assert self.moving0 in self.radar.scan_result
        self.ct.tick(2)
        assert self.moving0 not in self.radar.scan_result
