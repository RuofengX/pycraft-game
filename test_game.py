import unittest
import pickle

from objprint import op  # type:ignore

from game import Core


class TestCore(unittest.TestCase):
    def setUp(self):
        self.core = Core()

    def tearDown(self):
        pass

    def test_save(self):
        self.core.ct.world.report()
        self.core.save()
        with open(self.core.save_file_path, "rb") as f:
            obj = pickle.load(f)
            op(dir(obj))


if __name__ == '__main__':
    unittest.main()
