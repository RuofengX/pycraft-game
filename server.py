from dataclasses import dataclass
import base64
import pickle

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder

from pyworld.world import Entity
from pyworld.utils import RtnStatus, ReturnResult
from game import Core


@dataclass
class ServerRtn(ReturnResult):
    """Easy way to create json response."""

    def entity(self, entity: Entity):
        """Create a success responde
        with detail={'dict':..., 'obj_pickle':...}."""
        self.status = RtnStatus.SUCCESS
        obj_pickle_base64 = base64.b64encode(pickle.dumps(entity))
        self.detail = {
            "dict": entity.__getstate__(),
            "obj_pickle_base64": str(obj_pickle_base64),
        }
        return self.to_json()

    def to_json(self) -> str:
        """
        Use fastapi jsonable encoder to
        override the default json.dumps
        """
        return jsonable_encoder(self.to_dict())


app = FastAPI()
core = Core("./save-301286.bin")
# core = Core()


@app.on_event("startup")
async def startup_event():
    core.start()


@app.on_event("shutdown")
async def shutdown_event():
    core.save()


@app.get(path="/player/{username}")
async def get_player_info(username: str, passwd: str):
    """Get player info."""
    rtn = ServerRtn()
    if username not in core.player_dict.keys():
        return rtn.fail("Username not registered yet.")

    else:
        if core.player_dict[username].passwd_with_salt == passwd:
            p = core.player_dict[username]
            return rtn.entity(p)
        else:
            return rtn.fail("Password checking not passed.")


@app.get(path="/register/{username}")
async def player_register(username: str, passwd: str):
    """Register new player."""
    rtn = ServerRtn()

    if username in core.player_dict.keys():
        return rtn.fail(message="Username already registered.")
    else:
        p = core.register(username, passwd)
        return rtn.entity(p)
