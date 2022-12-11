import time
import unittest
from dataclasses import dataclass
from pprint import pprint as print

from objprint import op  # type:ignore

from pyworld.modules import Cargo, CargoMixin, DebugMixin, Item, MsgMixin
from pyworld.world import Character, Continuum, Vector


class DebugEntity(DebugMixin, Character):
    pass


class TestDebugMixin(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.db_ent = self.ct.world.world_new_entity(
            cls=DebugEntity, pos=Vector(0, 0, 0)
        )
        self.db_ent._report_flag = True

    @unittest.skip("passed")
    def test_log(self):
        print(self.db_ent.__class__.mro())
        op(self.db_ent.__class__.__dict__)
        op(dir(self.db_ent))

    @unittest.skip("passed")
    def test_basic(self):
        self.ct.start()
        time.sleep(1)

    def tearDown(self):
        self.ct.stop()


class MsgEntity(MsgMixin, Character):
    pass


class TestMsgMixin(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.ent0 = self.ct.world.world_new_character(pos=Vector(0, 0, 0))
        self.msg0 = self.ct.world.world_new_entity(
            cls=MsgEntity, pos=Vector(0, 0, 0), velo=Vector(0, 0, 0)
        )
        self.msg1 = self.ct.world.world_new_entity(
            cls=MsgEntity, pos=Vector(10, 0, 0), velo=Vector(0, 0, 0)
        )
        self.msg2 = self.ct.world.world_new_entity(
            cls=MsgEntity, pos=Vector(10, 0, 0), velo=Vector(-0.1, 0, 0)
        )

    def tearDown(self):
        self.ct.stop()

    def test_msg_duck_type(self):
        assert MsgMixin._msg_target_has_inbox(self.ent0) is False
        self.ent0.msg_inbox = []  # type: ignore
        assert MsgMixin._msg_target_has_inbox(self.ent0) is True
        assert MsgMixin._msg_target_has_inbox(self.msg0)

    def test_msg_send(self):
        self.ct.start()
        self.msg0.msg_radius = 0.001
        self.msg0.msg_send(self.msg1.eid, b"test, radius=0.001")
        self.msg0.msg_radius = 10
        self.msg0.msg_send(self.msg1.eid, b"test, radius=10")
        self.msg0.msg_radius = 1000
        self.msg0.msg_send(self.msg1.eid, b"test, radius=1000")
        time.sleep(1)
        assert self.msg1.msg_inbox == [b"test, radius=10", b"test, radius=1000"]

    def test_msg_ensure(self):
        self.msg0.msg_radius = 5
        self.msg0.msg_send_ensure(self.msg2.eid, b"test, ensure")
        self.ct.start()
        time.sleep(1)
        assert self.msg2.msg_inbox == [b"test, ensure"]


class CargoEntity(CargoMixin, Character):
    pass


@dataclass
class Ore(Item):
    mass = 1


class TestCargo(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.ent0 = self.ct.world.world_new_character(pos=Vector(0, 0, 0))
        self.crg0 = self.ct.world.world_new_entity(
            cls=CargoEntity, pos=Vector(0, 0, 0), cargo_max_slots=10
        )
        self.crg1 = self.ct.world.world_new_entity(
            cls=CargoEntity, pos=Vector(10, 0, 0), cargo_max_slots=100
        )
        self.crg2 = self.ct.world.world_new_entity(
            cls=CargoEntity, pos=Vector(10, 0, 0), cargo_max_slots=1
        )

    def tearDown(self):
        self.ct.stop()

    def test_cargo_add_stack(self):
        self.crg0._report_flag = True
        self.crg0._cargo_add(Ore().to_stack())
        assert tuple(self.crg0.cargo) == tuple(Cargo((Ore().to_stack())))

    def test_cargo_max_slot(self):
        self.crg0._report_flag = True
        self.ct.start()

        self.crg0._cargo_add(Ore().to_stack())
        assert self.crg0.cargo_has_slot()

        for i in range(100):
            self.crg0._cargo_add(Ore().to_stack())
        assert self.crg0.cargo_has_slot()
        assert len(self.crg0.cargo) == 1

        time.sleep(1)

    def test_cargo_mass(self):
        self.ct.start()
        self.crg0._cargo_add(Ore().to_stack())
        assert self.crg0.cargo.mass == 1
        time.sleep(1)

    def test_cargo_pop(self):
        self.ct.start()
        self.crg1._cargo_add(Ore())
        assert hasattr(self.crg1.cargo, "Ore")
        self.crg1._cargo_pop(name="Ore")
        assert not hasattr(self.crg1.cargo, "Ore")


if __name__ == "__main__":
    unittest.main()
