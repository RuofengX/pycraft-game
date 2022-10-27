from unittest import TestCase, skip, main

from fastapi.encoders import jsonable_encoder
from pprint import pprint
from objprint import op  # type: ignore

from server import ServerRtn
from pyworld.entity import Entity


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
