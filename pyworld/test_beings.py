import unittest
import time

from objprint import op  # type:ignore
from pprint import pprint

from .world import Continuum, Vector, Character, Entity
from .beings import DebugMixin, MsgMixin


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


class MsgEntity(MsgMixin, Character):
    pass


class TestMsgMixin(unittest.TestCase):
    def setUp(self):
        self.ct = Continuum()
        self.ent0 = self.ct.new_entity(cls=Entity)
        self.msg0 = self.ct.new_entity(
            cls=MsgEntity, pos=Vector(0, 0, 0), velo=Vector(0, 0, 0)
        )
        self.msg1 = self.ct.new_entity(
            cls=MsgEntity, pos=Vector(10, 0, 0), velo=Vector(0, 0, 0)
        )
        self.msg2 = self.ct.new_entity(
            cls=MsgEntity, pos=Vector(10, 0, 0), velo=Vector(-0.1, 0, 0)
        )

    def tearDown(self):
        self.ct.stop()

    def test_msg_duck_type(self):
        assert MsgMixin.msg_target_has_inbox(self.ent0) is False
        self.ent0.msg_inbox = []
        assert MsgMixin.msg_target_has_inbox(self.ent0) is True
        assert MsgMixin.msg_target_has_inbox(self.msg0)

    def test_msg_send(self):
        self.ct.start()
        self.msg0.msg_send(self.msg1.eid, b"test, radius=0.001", 0.001)
        self.msg0.msg_send(self.msg1.eid, b"test, radius=10", 10)
        self.msg0.msg_send(self.msg1.eid, b"test, radius=1000", 1000)
        time.sleep(1)
        assert self.msg1.msg_inbox == \
            [b"test, radius=10", b"test, radius=1000"]

    def test_msg_ensure(self):
        self.msg0.msg_send_ensure(self.msg2.eid, b"test, ensure", 1)
        self.ct.start()
        time.sleep(0.1)
        assert self.msg2.msg_inbox == [b"test, ensure"]


if __name__ == "__main__":
    unittest.main()
