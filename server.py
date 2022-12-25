import asyncio as aio
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from game import Core
from pyworld.datamodels.function_call import (
    CallRequestModel,
    CallResultModel,
    ServerResultModel,
)
from pyworld.datamodels.property_cache import PropertyCache
from pyworld.datamodels.websockets import WSCommand, WSPayload, WSStage
from pyworld.player import Player


class Server(FastAPI):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.core = Core(os.environ.get("PYWORLD_SAVE_PATH"))

        @self.on_event("startup")
        async def startup_event():
            self.core.start()

        @self.on_event("shutdown")
        async def shutdown_event():
            self.core.stop()

        @self.get(path="/player")
        async def player_get_info(username: str, passwd: str):
            """Get player info."""

            rtn = ServerResultModel()
            if not self.core.check_login(username, passwd):
                return rtn.passwd_check_fail()

            p = self.core.player_dict[username]

            return ServerResultModel().entity(p)

        @self.get(path="/register")
        async def register(username: str, passwd: str) -> ServerResultModel:
            """Register new player."""
            rtn = ServerResultModel()

            if username in self.core.player_dict:
                return rtn.name_already_used()

            p = self.core.register(username, passwd)
            return ServerResultModel().entity(p)

        @self.get(path="/ctrl/list-method")
        async def ctrl_list_method(username: str, passwd: str) -> ServerResultModel:
            """Get all controllable methods names and docs."""
            rtn = ServerResultModel()

            if not self.core.check_login(username, passwd):
                return rtn.passwd_check_fail()

            p = self.core.player_dict[username]

            return rtn.success(p.ctrl_list_method())

        @self.get(path="/ctrl/get-property/{key_name}")
        async def ctrl_get_properties(
            username: str, passwd: str, key_name: str
        ) -> ServerResultModel:
            """Get one specificial properties."""
            rtn = ServerResultModel()

            if not self.core.check_login(username, passwd):
                return rtn.passwd_check_fail()

            p = self.core.player_dict[username]

            try:
                value = p.ctrl_get_property(key_name)
                rtn.success(value)
            except KeyError as e:
                rtn.fail(f"Key {key_name} not found.", e)
            finally:
                return rtn

        @self.get(path="/ctrl/list-property")
        async def ctrl_list_properties(username: str, passwd: str) -> ServerResultModel:
            """Get all controllable properties."""

            rtn = ServerResultModel()

            if not self.core.check_login(username, passwd):
                return rtn.passwd_check_fail()

            p: Player = self.core.player_dict[username]

            return rtn.success(p.ctrl_list_property())

        @self.post(path="/ctrl/call")
        async def ctrl_call(
            *, username: str, passwd: str, body: CallRequestModel
        ) -> ServerResultModel:
            rtn = ServerResultModel()

            if not self.core.check_login(username, passwd):
                rtn.passwd_check_fail()

            if username not in self.core.player_dict:
                return rtn.name_not_valid()

            p: Player = self.core.player_dict[username]

            result: CallResultModel = p.ctrl_safe_call(body)
            rtn.success(result.to_dict())
            return rtn

        @self.websocket(path="/ctrl/stream")
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
            if not self.core.check_login(username, passwd):
                payload.close(stage, reason="credential wrong")
                await payload.send_ws(ws)
                await ws.close()

            p: Player = self.core.player_dict[username]
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
                            payload.close(
                                stage, reason="Client send the CLOSE command."
                            )
                        case WSCommand.ALL:
                            payload.all(stage, detail=cache.get_entity_property(ent=p))
                        case WSCommand.DIFF:
                            payload.diff(stage, detail=cache.get_diff_property(ent=p))
                        case WSCommand.CMD:
                            client_patch = CallRequestModel(**client_req.detail)
                            payload.cmd(server_resp=p.ctrl_safe_call(data=client_patch))

                    # STAGE SERVER_SEND
                    payload.stage = WSStage.SERVER_SEND
                    await payload.send_ws(ws)

                except ValueError as e:
                    stop_flag = True
                    payload.close(stage, "ValueError", e)

                except AssertionError as e:
                    stop_flag = True
                    payload.close(stage, "AssertionError", e)
                    await payload.send_ws(ws)

                except WebSocketDisconnect:
                    stop_flag = True
                    payload.close(stage, "WebSocketDisconnect")

                except Exception as e:
                    stop_flag = True
                    payload.close(stage, "UnexpectedError", e)

                finally:
                    if stop_flag:
                        try:
                            await aio.wait([ws.close()], timeout=5.0)
                        except Exception:
                            pass
