import base64
import os
import pickle
import unittest

from fastapi.testclient import TestClient
from requests import Response

from pyworld.modules.item import Item
from pyworld.player import Player
from server import app, core


class TargetItem(Item):
    mass = 0


core.start()


class TestNetwork(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app=app, base_url="http://localhost:8000")
        self.core = core
        self.world = core.ct.world

    def tearDown(self) -> None:
        try:
            os.remove(self.core.save_file_path)
        except Exception:
            pass

    def test_register(self) -> None:
        params = {
            "username": "test1",
            "passwd": "1",
        }
        response: Response = self.client.get("/register", params=params)
        assert response.status_code == 200
        assert response.json()["status"] == "Success"
        assert self.world.entity_dict != {}
        eid = response.json()['detail']['dict']['eid']

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

    def test_get_property(self) -> None:
        params = {
            "username": "test2",
            "passwd": "2",
        }
        eid = self.core.register(**params).eid

        response: Response = self.client.get("/ctrl/get-property", params=params)
        assert response.status_code == 200
        assert response.json()["status"] == "Success"
        player_c = response.json()["detail"]
        player_s = self.world.entity_dict[eid].get_state()
        compare_list = ["uuid", "eid", "username", "passwd"]
        for entry in compare_list:
            assert player_s[entry] == player_c[entry]
