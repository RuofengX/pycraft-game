import base64
import json
from dataclasses import dataclass
from typing import Any, Dict

import dictdiffer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from game import Core
from pyworld.control import ControlMixin
from pyworld.player import Player
from pyworld.utils import Result, RtnStatus
from pyworld.world import Entity
from utils import ClientCommand


@dataclass
class ServerRtn(Result):
    """
    Easy way to create json response.

    Extend some useful fail states.
    """

    stage = "Server"

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
        return self.fail("Username not registered yet.")

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

# TODO: Add auth middleware


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


@app.get(path="/ctrl/get-method")
async def ctrl_get_method(username: str, passwd: str):
    """Get all controllable methods names and docs."""
    rtn = ServerRtn()

    if not core.check_login(username, passwd):
        return rtn.passwd_check_fail()

    p = core.player_dict[username]

    return rtn.success(p.ctrl_list_method())


@app.get(path="/ctrl/get-property")
async def ctrl_get_properties(username: str, passwd: str):
    """Get all controllable properties."""

    rtn = ServerRtn()

    if not core.check_login(username, passwd):
        return rtn.passwd_check_fail()

    p: Player = core.player_dict[username]

    return rtn.success(p.ctrl_list_property())


@app.put(path="/ctrl/call")
async def ctrl_call(*, username: str, passwd: str, func_name: str, keywords: dict):
    rtn = ServerRtn()

    if not core.check_login(username, passwd):
        rtn.passwd_check_fail()

    if username not in core.player_dict:
        return rtn.name_not_valid()

    p: Player = core.player_dict[username]

    result: Result = p.ctrl_safe_call(func_name, **keywords)
    rtn.success(result.to_dict())
    return rtn.to_json()


class PropertyCache(Dict[int, dict]):
    """
    Temp Memorize cache,

    Used to transfer diff data in websocket connection
    """

    def __init__(self):
        super().__init__(self)

    def get_raw(self, ent: ControlMixin) -> Dict[str, Any]:
        return ent.ctrl_list_property()

    def get_entity_property(self, ent: ControlMixin) -> str:
        rtn = self.get_raw(ent)
        self[ent.uuid] = rtn
        return json.dumps(rtn)

    def get_diff_property(self, ent: ControlMixin) -> str:
        ent_id = ent.uuid
        raw: dict = self.get_raw(ent)
        if ent_id not in self:
            self[ent_id] = {}
        diff = list(dictdiffer.diff(self[ent.uuid], raw))
        self[ent.uuid] = raw
        return json.dumps({"diff": diff})


# TODO: Test Needed
@app.websocket(path="/ctrl/diff")
async def ctrl_diff(
    *,
    ws: WebSocket,
    username: str,
    passwd: str,
) -> None:
    await ws.accept()

    print((username, passwd))
    if not core.check_login(username, passwd):
        rtn = ServerRtn()
        return rtn.name_not_valid()

    p: Player = core.player_dict[username]
    cache = PropertyCache()
    stop_flag: bool = False

    while not stop_flag:
        try:
            client_cmd = await ws.receive_text()  # receive first
            cmd = ClientCommand(client_cmd)  # raise ValueError
            if cmd is ClientCommand.FULL:
                await ws.send_text(cache.get_entity_property(p))
            elif cmd is ClientCommand.DIFF:
                await ws.send_text(cache.get_diff_property(p))
            elif cmd is ClientCommand.DONE:
                stop_flag = True

        except ValueError:
            stop_flag = True
            await ws.close()

        except WebSocketDisconnect:
            stop_flag = True
