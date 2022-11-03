from dataclasses import dataclass
from enum import Enum
import base64
import pickle

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder

from pyworld.world import Entity
from game import Core


class RtnStatus(Enum):
    SUCCESS = "Success"
    FAIL = "Fail"
    NOT_SET = "<Not_set>"


@dataclass
class ServerRtn:
    """Easy way to create json response."""

    status: RtnStatus = RtnStatus.NOT_SET
    detail: dict | str = "Nothing to say here."

    def fail(self, message: str | dict):
        """Create a fail responde with detail=message."""
        self.status = RtnStatus.FAIL
        self.detail = message
        return self.to_json()

    def success(self, message: str | dict):
        """Create a success responde with detail=message."""
        self.status = RtnStatus.SUCCESS
        self.detail = message
        return self.to_json()

    def entity(self, entity: Entity):
        """Create a success responde
        with detail={'dict':..., 'obj_pickle':...}."""
        self.status = RtnStatus.SUCCESS
        obj_pickle_base64 = base64.b64encode(pickle.dumps(entity))
        self.detail = {
            "dict": entity.__getstate__(),
            "obj_pickle_base64": obj_pickle_base64,
        }
        return self.to_json()

    def to_dict(self):
        return {"status": self.status.value, "detail": self.detail}

    def to_json(self):
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
