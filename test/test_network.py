import unittest
import base64
import pickle
import os

from fastapi.testclient import TestClient
from httpx import Response
from pyworld.datamodels.function_call import ServerReturnModel
from pyworld.modules.item import Item
from pyworld.player import Player

from server import app, core


class TargetItem(Item):
    mass = 0


class TestNetwork(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app=app, base_url="http://localhost:8000")
        self.core = core
        self.world = core.ct.world
        self.core.start()
        self.id_params = {
            'username': 'test',
            'passwd': '1',
        }

    def tearDown(self) -> None:
        self.core.stop()
        os.remove(self.core.save_file_path)

    def test_register(self) -> None:
        response: Response = self.client.get(f"/register", params=self.id_params)
        assert response.status_code == 200
        assert self.world.entity_dict != {}

        player_s = self.world.entity_dict[1].get_state()
        player_c = response.json()['detail']['dict']
        compare_list = ['uuid', 'eid', 'username', 'passwd']
        for entry in compare_list:
            assert player_s[entry] == player_c[entry]

        player_c_bytes = pickle.loads(
            base64.b64decode(
                bytes(
                    response.json()['detail']['obj_pickle_base64'], encoding='utf-8'
                )
            )
        )
        assert isinstance(player_c_bytes, Player)
        compare_list = ['uuid', 'eid', 'username', 'passwd']
        for entry in compare_list:
            assert player_s[entry] == player_c_bytes.get_state()[entry]
    
    def test_get_property(self) -> None:
        response: Response = self.client.get(f"/ctrl/get-property", params=self.id_params)
        assert response.status_code == 200
        # TODO:
    
