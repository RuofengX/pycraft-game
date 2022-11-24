import base64
from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder

from game import Core
from pyworld.player import Player
from pyworld.utils import Result, RtnStatus
from pyworld.world import Entity


@dataclass
class ServerRtn(Result):
    """
    Easy way to create json response.

    Extend some useful fail states.
    """

    stage = 'Server'

    def entity(self, entity: Entity) -> str:
        """
        Create a success respond
        with detail={'dict':..., 'obj_pickle':...}.
        """

        obj_pickle_base64 = base64.b64encode(entity.get_state_b())
        self.status = RtnStatus.SUCCESS
        self.detail = {
            "dict": entity.get_state(),
            "obj_pickle_base64": str(obj_pickle_base64),
        }
        return self.to_json()

    def name_not_valid(self) -> str:
        return self.fail("Username not registered yet.").to_json()

    def name_already_used(self) -> str:
        return self.fail("Username already used.")

    def passwd_check_fail(self) -> str:
        return self.fail("Password check not pass.")

    def to_json(self) -> str:
        """
        Use fastapi jsonable encoder to
        override the default json.dumps
        """
        return jsonable_encoder(self.to_dict())


app = FastAPI()
core = Core("./save-301286.bin")
# core = Core()

# TODO: Add temp token that no need to use passwd every time.


@app.on_event("startup")
async def startup_event():
    core.start()


@app.on_event("shutdown")
async def shutdown_event():
    core.stop()


@app.get(path="/player/{username}")
async def player_get_info(username: str, passwd: str):
    """Get player info."""

    rtn = ServerRtn()
    if not core.check_login(username, passwd):
        return rtn.passwd_check_fail()

    p = core.player_dict[username]

    return ServerRtn().entity(p)


@app.get(path="/register")
async def register(username: str, passwd: str):
    """Register new player."""
    rtn = ServerRtn()

    if username in core.player_dict:
        return rtn.name_already_used()

    p = core.register(username, passwd)
    return rtn.entity(p)


@app.get(path="/ctrl/get/method")
async def ctrl_get_method(username: str, passwd: str):
    """Get all controllable methods names and docs."""
    rtn = ServerRtn()

    if not core.check_login(username, passwd):
        return rtn.passwd_check_fail()

    p = core.player_dict[username]

    return rtn.success(
        p.ctrl_list_method()
    )


@app.get(path="/ctrl/get/property")
async def ctrl_get_properties(username: str, passwd: str):
    """Get all controllable properties."""
    rtn = ServerRtn()

    if not core.check_login(username, passwd):
        return rtn.passwd_check_fail()

    p: Player = core.player_dict[username]

    return rtn.success(
        p.ctrl_list_property()
    )


@app.put(path="/ctrl/run")
async def ctrl_run(
    *,
    username: str, passwd: str, func_name: str, keywords: dict
):
    rtn = ServerRtn()

    if not core.check_login(username, passwd):
        rtn.passwd_check_fail()

    if username not in core.player_dict:
        return rtn.name_not_valid()

    p: Player = core.player_dict[username]

    result: Result = p.ctrl_safe_call(func_name, **keywords)
    rtn.success(result.to_dict())
    return rtn.to_json()
