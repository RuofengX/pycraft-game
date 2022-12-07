from unittest import TestCase, main, skip

from aiounittest import AsyncTestCase
from fastapi.encoders import jsonable_encoder
from objprint import op  # type: ignore
from objprint import op as print
from websockets.client import connect

from pyworld.entity import Entity
from server import ServerRtn


class TestServerRtn(TestCase):
    def setUp(self):
        self.rtn = ServerRtn()
        self.ent = Entity(eid=1)

    @skip("passed")
    def test_entity(self):
        self.rtn.entity(self.ent)
        op(self.rtn)
        print(self.rtn.to_json())

    @skip("passed")
    def test_jsonable_encoder(self):
        self.rtn.entity(self.ent)
        op(self.rtn)
        print(jsonable_encoder(self.rtn))


class TestWebSocket(AsyncTestCase):
    @skip("mask")
    async def test_full(self):
        async with connect(
            "ws://localhost:8000/ctrl/diff?username=ruofeng&passwd=111111"
        ) as conn:
            await conn.send("full")
            recv = await conn.recv()
            print(recv)

    async def test_diff(self):
        async with connect(
            "ws://localhost:8000/ctrl/diff?username=ruofeng&passwd=111111"
        ) as conn:
            await conn.send("full")
            await conn.recv()
            import time

            time.sleep(1)
            await conn.send("diff")
            recv = await conn.recv()
            import json

            result = json.loads(recv)
            print(result)

    async def test_call(self):






if __name__ == "__main__":
    main()
