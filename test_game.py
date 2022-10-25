import time
import unittest
import pickle

from objprint import op  # type:ignore

from game import Core


class TestCore(unittest.TestCase):
    def setUp(self):
        self.core = Core()
        self.core.ct.world.report_flag = True

    def tearDown(self):
        self.core.ct.stop()

    def test_save(self):
        dic0 = self.core.ct.world.__dict__
        self.core.start()
        time.sleep(1)
        self.core.save()
        with open(self.core.save_file_path, "rb") as f:
            obj = pickle.load(f)
        dic1 = obj.__dict__.copy()
        op(dic0)
        op(dic1)
        assert dic0['entity_dict'] == dic1['entity_dict']


if __name__ == '__main__':
    unittest.main()
