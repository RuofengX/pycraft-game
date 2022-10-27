import time
import unittest
import pickle

from objprint import op  # type:ignore

from game import Core
from pyworld.basic import Vector


class TestCore(unittest.TestCase):
    def setUp(self):
        self.core = Core()
        self.core.ct.world.world_new_character(pos=Vector(0, 1, 0))
        # self.core.ct.world.report_flag = True

    def tearDown(self):
        self.core = None

    def test_save(self):
        dic0 = self.core.ct.world.__dict__
        self.core.start()
        time.sleep(1)
        # self.core.save()
        self.core.stop()
        with open(self.core.save_file_path, "rb") as f:
            obj = pickle.load(f)
        dic1 = obj.__dict__.copy()
        op(dic0)
        op(dic1)
        assert dic0['entity_dict'] == dic1['entity_dict']

    def test_stop(self):
        dic0 = self.core.ct.world.__dict__
        op(self.core)
        self.core.start()
        time.sleep(1)
        self.core.stop()
        time.sleep(1)

        with open(self.core.save_file_path, "rb") as f:
            obj = pickle.load(f)
        dic1 = obj.__dict__.copy()
        op(dic0)
        op(dic1)
        assert dic0['entity_dict'] == dic1['entity_dict']


if __name__ == '__main__':
    unittest.main()
