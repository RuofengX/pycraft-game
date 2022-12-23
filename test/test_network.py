import base64
import os
import pickle
import unittest

from fastapi.testclient import TestClient
from pyworld.datamodels.function_call import CallRequestModel
from pyworld.modules.equipments.radar import Radar

from pyworld.modules.item import Item
from pyworld.player import Player
from server import Server


class TargetItem(Item):
    mass = 0


class TestServer(unittest.TestCase):
    def setUp(self) -> None:
        self.server = Server()
        self.server.core.start()
        self.client = TestClient(app=self.server, base_url="http://localhost:8000")
        self.world = self.server.core.ct.world
        self.params = {
            "username": "test",
            "passwd": "1",
        }

    def tearDown(self) -> None:
        try:
            self.server.core.stop()
            os.remove(self.server.core.save_file_path)
        except Exception:
            pass

    def test_register(self) -> None:
        response = self.client.get("/register", params=self.params)
        assert response.status_code == 200
        assert response.json()["status"] == "Success"
        assert self.world.entity_dict != {}
        eid = response.json()["detail"]["dict"]["eid"]

        player_s = self.world.world_get_entity(eid).get_state()
        player_c = response.json()["detail"]["dict"]
        compare_list = ["uuid", "eid", "username", "passwd"]
        for entry in compare_list:
            assert player_s[entry] == player_c[entry]

        player_c_bytes = pickle.loads(
            base64.b64decode(
                bytes(response.json()["detail"]["obj_pickle_base64"], encoding="utf-8")
            )
        )
        assert isinstance(player_c_bytes, Player)
        compare_list = ["uuid", "eid", "username", "passwd"]
        for entry in compare_list:
            assert player_s[entry] == player_c_bytes.get_state()[entry]

    def test_ctrl_get_property(self) -> None:
        eid = self.server.core.register(**self.params).eid
        player_s: Player = self.world.world_get_entity(eid)
        assert player_s is not None
        radar = self.world.world_new_entity(
            cls=Radar,
        )
        player_s._equip_add(radar)
        response = self.client.get("/ctrl/get-property", params=self.params)
        assert response.status_code == 200
        assert response.json()["status"] == "Success"
        player_c = response.json()["detail"]
        compare_list = ["uuid", "eid", "username", "passwd"]
        for entry in compare_list:
            assert player_s.get_state()[entry] == player_c[entry]

    def test_ctrl_get_method(self) -> None:
        def you_got_me():
            """
            This is test.
            """
            pass

        def _not_see_me():
            pass

        eid = self.server.core.register(**self.params).eid
        player_s = self.server.core.ct.world.world_get_entity(eid)

        setattr(player_s, "you_got_me", you_got_me)
        setattr(player_s, "_not_see_me", _not_see_me)

        response = self.client.get("/ctrl/get-method", params=self.params)
        assert response.status_code == 200
        assert response.json()["status"] == "Success"
        player_method_c = response.json()["detail"]

        assert "you_got_me" in player_method_c
        assert "_not_see_me" not in player_method_c
        assert "This is test." == player_method_c["you_got_me"]

        delattr(player_s, "you_got_me")
        delattr(player_s, "_not_see_me")

    def test_call(self) -> None:
        eid = self.server.core.register(**self.params).eid
        player_s: Player = self.world.world_get_entity(eid)

        def echo(input: str) -> str:
            return input

        setattr(player_s, "echo", echo)

        request = CallRequestModel(func_name="echo", kwargs={"input": "Hello World"})
        response = self.client.post(
            "/ctrl/call", params=self.params, json=request.dict()
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "Success"
        assert result["detail"]["detail"] == "Hello World"

    def test_ws(self) -> None:
        pass
