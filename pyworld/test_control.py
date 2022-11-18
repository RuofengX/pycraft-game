import unittest
from pprint import pprint as print

from pyworld.world import Continuum
from pyworld.control import ControlMixin
from pyworld.basic import Vector
from pyworld.modules import (
    DebugMixin,
    MsgMixin,
    StructMixin,
    CargoMixin,
    BodyMixin,
)


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
