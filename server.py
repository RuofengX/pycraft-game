import asyncio as aio
import base64

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from game import Core
from pyworld.player import Player
from pyworld.datamodels.function_call import RequestModel, ResultModel, RtnStatus
from pyworld.entity import Entity
from pyworld.datamodels.websockets import WSCommand, WSPayload, WSStage
from pyworld.datamodels.property_cache import PropertyCache


class ServerRtn(ResultModel):
    """
    Easy way to create json response.

    Extend some useful fail states.
    """

    stage: str = "Server"

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


@app.post(path="/ctrl/call")
async def ctrl_call(*, username: str, passwd: str, body: RequestModel):
    rtn = ServerRtn()

    if not core.check_login(username, passwd):
        rtn.passwd_check_fail()

    if username not in core.player_dict:
        return rtn.name_not_valid()

    p: Player = core.player_dict[username]

    result: ResultModel = p.ctrl_safe_call(body)
    rtn.success(result.to_dict())
    return rtn.to_json()


@app.websocket(path="/ctrl/stream")
async def ctrl_stream(
    *,
    ws: WebSocket,
    username: str,
    passwd: str,
) -> None:

    payload: WSPayload = WSPayload()

    # STAGE INIT
    stage = WSStage.INIT
    await ws.accept()

    # STAGE CHECK
    stage = WSStage.LOGIN
    if not core.check_login(username, passwd):
        payload.close(stage, reason="credential wrong")
        await payload.send_ws(ws)
        await ws.close()

    p: Player = core.player_dict[username]
    cache: PropertyCache = PropertyCache()
    stop_flag: bool = False

    # STAGE LOOP
    while not stop_flag:
        try:
            # STAGE CLIENT_PREPARE
            pass

            # STAGE CLIENT_SEND
            stage = WSStage.CLIENT_SEND
            client_req: WSPayload = await WSPayload.from_read_ws(ws)
            assert client_req.stage is WSStage.CLIENT_SEND
            client_cmd = client_req.command

            # STAGE SERVER_PREPARE
            stage = WSStage.SERVER_PREPARE

            match client_cmd:
                case WSCommand.PING:
                    payload.ping(stage)
                case WSCommand.CLOSE:
                    stop_flag = True
                    payload.close(stage, reason="Client send the CLOSE command.")
                case WSCommand.ALL:
                    payload.all(stage, detail=cache.get_entity_property(ent=p))
                case WSCommand.DIFF:
                    payload.diff(stage, detail=cache.get_diff_property(ent=p))
                case WSCommand.CMD:
                    client_patch = RequestModel(**client_req.detail)
                    payload.cmd(
                        server_resp=p.ctrl_safe_call(
                            data=client_patch
                        )
                    )

            # STAGE SERVER_SEND
            payload.stage = WSStage.SERVER_SEND
            await payload.send_ws(ws)

        except ValueError as e:
            stop_flag = True
            payload.close(stage, 'ValueError', e)

        except AssertionError as e:
            stop_flag = True
            payload.close(stage, 'AssertionError', e)
            await payload.send_ws(ws)

        except WebSocketDisconnect:
            stop_flag = True
            payload.close(stage, 'WebSocketDisconnect')

        except Exception as e:
            stop_flag = True
            payload.close(stage, 'UnexceptedError', e)

        finally:
            if stop_flag:
                try:
                    await aio.wait([ws.close()], timeout=5.0)
                except Exception:
                    pass
