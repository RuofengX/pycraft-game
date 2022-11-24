import unittest
from pprint import pprint as print

from pyworld.basic import Vector
from pyworld.control import ControlMixin
from pyworld.modules import (BodyMixin, CargoMixin, DebugMixin, MsgMixin,
                             StructMixin)
from pyworld.world import Continuum


class AllInOneEntity(
    DebugMixin,
    MsgMixin,
    StructMixin,
    CargoMixin,
    BodyMixin,
    ControlMixin,
):
    pass


class TestControl(unittest.TestCase):

    def setUp(self):
        self.ct = Continuum()
        self.a1 = self.ct.world.world_new_entity(AllInOneEntity, pos=Vector(0, 0, 0))

    def test_list_method(self):
        print(self.a1.ctrl_list_method())

    def test_list_properties(self):
        print(self.a1.ctrl_list_property())


if __name__ == '__main__':
    unittest.main()
