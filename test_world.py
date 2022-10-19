import unittest
import time
from objprint import op  # type:ignore
from world import Continuum, Vector


class TestCharacter(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.test_character = self.ct.new_character(Vector(0, 0, 0))

    @unittest.skip("passed")
    def test_new_character(self):
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


class TestWorld(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.test_char = self.ct.new_character(pos=Vector(0, 0, 0))
        self.test_char2 = self.ct.new_character(pos=Vector(10, 0, 0))
        self.test_char2.velocity = Vector(-0.001, 0, 0)

    @unittest.skip("passed")
    def test_get_entity(self):
        eid = self.test_char.eid
        self.ct.start()
        time.sleep(1)
        op(self.ct.get_entity(eid))
        time.sleep(1)

    @unittest.skip("passed")
    def test_get_character_nearby(self):
        ls = self.ct.get_character_nearby(self.test_char, 100)
        op(ls)
        self.ct.start()
        time.sleep(1)

    @unittest.skip("passed")
    def test_nearby_when_running(self):
        self.ct.start()
        while 1:
            ls = self.ct.get_character_nearby(self.test_char, 1)
            if ls:
                op(ls)

    def tearDown(self):
        self.ct.stop()


if __name__ == "__main__":
    unittest.main()
