import unittest

from pyworld.basic import Vector
from pyworld.entity import Entity
from pyworld.modules.equipment import Equipment, EquipmentMixin
from pyworld.modules.equipments.radar import Radar
from pyworld.world import Character, Continuum


class EquipTargetEntity(EquipmentMixin, Entity):
    pass


class NotExist:
    pass


class TestModule(Equipment):
    require_module = EquipTargetEntity
    limit_num = 3


class TestReqModule(Equipment):
    require_module = NotExist


class TestLimitModule(Equipment):
    limit_num = 0


class TestEquipBase(unittest.TestCase):
    def setUp(self) -> None:
        self.ent = EquipTargetEntity()

    def test_ensure_feature(self) -> None:
        assert not self.ent._equip_add(TestReqModule())
        assert not self.ent._equip_add(TestLimitModule())
        assert self.ent.equip_list == []

    def test_equip_on(self) -> None:
        eqp = TestModule()
        self.ent._equip_add(eqp)
        assert self.ent.equip_list == [eqp]

    def test_limit(self) -> None:
        assert self.ent._equip_available_num(TestModule) == TestModule.limit_num
        eqp = TestModule()
        assert self.ent._equip_add(eqp)
        assert self.ent._equip_available_num(TestModule) == TestModule.limit_num - 1
        assert self.ent._equip_add(eqp)
        assert self.ent._equip_available_num(TestModule) == TestModule.limit_num - 2
        assert self.ent._equip_add(eqp)
        assert self.ent._equip_available_num(TestModule) == TestModule.limit_num - 3
        assert not self.ent._equip_add(eqp)
        assert self.ent._equip_available_num(TestModule) == TestModule.limit_num - 3


    def test_pop(self) -> None:
        eqp = TestModule()
        assert self.ent._equip_add(eqp)
        assert self.ent._equip_pop("TestModule") == eqp
        assert self.ent.equip_list == []
    
    def test_get(self) -> None:
        eqp = TestModule()
        eqp_2 = TestModule()
        assert self.ent._equip_add(eqp)
        assert self.ent._equip_add(eqp)
        assert self.ent._equip_add(eqp_2)

        assert self.ent._equip_get(TestModule) == eqp
        assert self.ent._equip_get('TestModule') == eqp

        assert self.ent._equip_get(TestModule, 1) == eqp
        assert self.ent._equip_get('TestModule', 1) == eqp

        assert self.ent._equip_get(TestModule, 2) == eqp_2
        assert self.ent._equip_get('TestModule', 2) == eqp_2

class TestRadar(unittest.TestCase):
    class NoPosition(EquipmentMixin, Entity):
        pass

    class Position(EquipmentMixin, Character):
        pass

    def setUp(self) -> None:
        self.ct = Continuum()
        self.radar = Radar()
        self.no_position = self.ct.world.world_new_entity(
            cls=self.NoPosition
        )
        self.position = self.ct.world.world_new_entity(
            cls=self.Position, pos=Vector(0, 0, 0)
        )
        for i in range(10):
            setattr(self, f'position{i}', self.ct.world.world_new_entity(
                cls=self.Position, pos=Vector(0, i, 0)
            ))
    
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
        self.radar.set_scan_tick(1)
        self.radar.radius = 0
        assert self.position._equip_add(self.radar)
        self.ct.world._tick()
        
