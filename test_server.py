from pprint import pprint
from unittest import TestCase, main, skip

from fastapi.encoders import jsonable_encoder
from objprint import op  # type: ignore

from pyworld.entity import Entity
from server import ServerRtn


class TestServerRtn(TestCase):

    def setUp(self):
        self.rtn = ServerRtn()
        self.ent = Entity(eid=1)

    @skip('passed')
    def test_entity(self):
        self.rtn.entity(self.ent)
        op(self.rtn)
        pprint(self.rtn.to_json())

    def test_jsonable_encoder(self):
        self.rtn.entity(self.ent)
        op(self.rtn)
        pprint(jsonable_encoder(self.rtn))


if __name__ == '__main__':
    main()
