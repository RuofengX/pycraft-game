import unittest

from pyworld.world import Continuum
from pyworld.modules import struct
from pyworld.basic import Vector


class TestStruct(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.struct = self.ct.world.world_new_entity(
            struct.StructMixin, pos=Vector(0, 0, 0)
        )
        self.ct.start()

    def tearDown(self):
        del self.struct
        self.ct.stop()

    def test_destroy(self):
        self.struct.destroy()
        assert self.struct.is_destroyed


if __name__ == "__main__":
    unittest.main()
