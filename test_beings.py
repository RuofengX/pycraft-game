import unittest
import time

from objprint import op  # type:ignore
from pprint import pprint

from world import Continuum, Vector, Character
from beings import DebugMixin, MsgMixin


class DebugEntity(DebugMixin, Character):
    pass


class TestDebugMixin(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.db_ent = self.ct.new_entity(cls=DebugEntity, pos=Vector(0, 0, 0))
        self.db_ent._report_flag = True

    @unittest.skip("passed")
    def test_log(self):
        pprint(self.db_ent.__class__.mro())
        op(self.db_ent.__class__.__dict__)
        op(dir(self.db_ent))

    @unittest.skip("passed")
    def test_basic(self):
        self.ct.start()
        time.sleep(1)

    def tearDown(self):
        self.ct.stop()


class MsgEntity(Character, MsgMixin):
    pass


class TestMsgMixin(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.ent0 = self.ct.new_entity(
            cls=MsgEntity, pos=Vector(0, 0, 0), velo=Vector(1, 0, 0)
        )
        self.db_ent._report_flag = True

    def tearDown(self):
        self.ct.stop()

    def test_send_msg(self):



if __name__ == "__main__":
    unittest.main()
