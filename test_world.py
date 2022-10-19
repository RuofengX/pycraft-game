import unittest
import time
from objprint import op  # type:ignore
from world import Continuum, Vector


class TestCharactor(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.test_character = self.ct.new_character(Vector(0, 0, 0))

    @unittest.skip("passed")
    def test_new_charactor(self):
        self.ct.start()
        self.ct.new_character(Vector(0, 0, 0))
        time.sleep(1)

    @unittest.skip("passed")
    def test_character_tick_func(self):
        self.ct.start()

        def tick_overload(belong: Continuum):
            # pprint(belong.entity_dict)
            op(belong)

        self.test_character.tick = tick_overload
        time.sleep(0.1)

    @unittest.skip("passed")
    def test_moving(self):
        self.test_character.velocity = Vector(1, 0, 0)

        def tick_overload(belong: Continuum):
            op(belong.entity_dict[1])

        self.ct.start()
        time.sleep(0.1)

    @unittest.skip("passed")
    def test_acc(self):
        self.test_character.acceleration = Vector(1, 0, 0)
        self.test_character._report_flag = True
        self.ct.start()
        time.sleep(0.1)

    def tearDown(self):
        self.ct.stop()


if __name__ == "__main__":
    unittest.main()
