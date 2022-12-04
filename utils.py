from __future__ import annotations

import base64
import json
import pickle
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Self, Type, cast, overload

import dictdiffer  # type: ignore
from fastapi import WebSocket

from pyworld.control import ControlMixin


class PropertyCache(Dict[int, dict]):
    """
    Temp Memorize cache,

    Used to transfer diff data in websocket connection
    """

    def __init__(self) -> None:
        super().__init__(self)

    def get_raw(self, ent: ControlMixin) -> Dict[str, Any]:
        return ent.ctrl_list_property()

    def get_entity_property(self, ent: ControlMixin) -> dict:
        rtn = self.get_raw(ent)
        self[ent.uuid] = rtn
        return rtn

    def get_diff_property(self, ent: ControlMixin) -> dict:
        ent_id: int = ent.uuid
        raw: dict = self.get_raw(ent)
        if ent_id not in self:
            self[ent_id] = {}
        diff: list = list(dictdiffer.diff(self[ent.uuid], raw))
        self[ent.uuid] = raw
        return {"diff": diff}


class EncodeMode(Enum):
    B64_PICKLE_BYTES = 0x0
    JSON = 0x1

    def __len__(self):
        return 2


@dataclass(init=True, repr=False)
class Payload:
    """
    Receive data container.

    # TODO: Use pydantic.BaseModel to do regulation
    # TODO: Test needed
    """

    default_encode: EncodeMode = EncodeMode.JSON

    @property
    def as_bytes(self, encode: Optional[EncodeMode] = None) -> bytes:
        if encode is None:
            encode = self.default_encode

        if encode is EncodeMode.B64_PICKLE_BYTES:
            return base64.b64encode(pickle.dumps(asdict(self)))
        elif encode is EncodeMode.JSON:
            return json.dumps(asdict(self)).encode("utf8")
        else:
            raise NotImplementedError("Unsupported encode.")

    @property
    def length(self) -> int:
        return len(self.as_bytes)

    @staticmethod
    def from_dict(d: dict) -> Payload:
        rtn: Payload = Payload()
        for key in d:
            setattr(rtn, key, d[key])
        return rtn

    @classmethod
    def from_bytes(cls: Type[Self], b: bytes, mode: EncodeMode | str) -> Self:
        if type(mode) == EncodeMode:
            pass
        else:
            try:
                mode = EncodeMode(mode)
            except TypeError as e:
                raise TypeError(f"Unsupported EncodeMode str.[{str(e)}]")

        match mode:
            case EncodeMode.B64_PICKLE_BYTES:
                rtn: Payload = pickle.loads(base64.b64decode(b))
            case EncodeMode.JSON:
                rtn: Payload = Payload.from_dict(json.loads(b.decode("utf8")))
            case other:
                raise NotImplementedError(f"Unsupported EncodeMode: {str(other)}")

        cast(cls, rtn)
        return rtn


class WebSocketStage(Enum):
    UNKNOWN = 0x00
    INIT = 0x10
    LOGIN = 0x20
    LOOP = 0x30
    CLIENT_PREPARE = 0x40
    CLIENT_SEND = 0x50
    SERVER_PREPARE = 0x60
    SERVER_SEND = 0x70

    def __len__(self):
        return 4


class WSCommand(Enum):
    """
    A brief protocol instruments:

    STAGE
    0. Just a simple States Machine

    INIT
    1. client send the GET request with credentials to ws uri,
    2. a ws created,
    LOGIN
    2.1. server check the credentials, if invalid -> (CLOSE, {})
    LOOP
    2.2. server send (CMD, {})
    CLIENT_PREPARE
    CLIENT_SEND
    2.3. client send CMD | ALL | DIFF | CLOSE
    SERVER_PREPARE
    SERVER_SEND
    2.4. server do the right response with correct WSCommand
    """

    PING = 0x00  # Server/Client, the peer should send the PING either.
    CLOSE = 0x01  # S: credentials is invalid
    CMD = 0x02  # S: ready for CMD | C: Call function, using **detail as kwargs
    ALL = 0x03  # C: need all info about the player entity
    DIFF = 0x04  # C: need diff info about the player entity


@dataclass
class WebSocketPayload(Payload):
    """
    Override: WebSocket use JSON to exchange data by force.
    Properties:
        stage: Record the stage for assert and debug use.
        command: the Command slot, mostly used by client, used to order the peer.
        detail: information body, mostly used by server,
            used to return the info that client asked.
    """

    default_encode: EncodeMode = field(default=EncodeMode.JSON, init=False)

    stage: WebSocketStage = field(default=WebSocketStage.UNKNOWN)
    command: WSCommand = WSCommand.PING
    detail: Dict[str, Any] = {}

    @staticmethod
    async def from_read_ws(ws: WebSocket) -> WebSocketPayload:
        return WebSocketPayload.from_bytes(
            await ws.receive_bytes(), mode=EncodeMode.JSON
        )

    def ping(self) -> WebSocketPayload:
        self.command = WSCommand.PING
        self.detail = {}
        return self

    def close(self, reason: str = "") -> WebSocketPayload:
        self.command = WSCommand.CLOSE
        self.detail = {
            "reason": reason,
        }
        return self

    def all(self, detail: dict) -> WebSocketPayload:
        self.command = WSCommand.ALL
        self.detail = detail
        return self

    def diff(self, detail: dict) -> WebSocketPayload:
        self.command = WSCommand.DIFF
        self.detail = detail
        return self

    @overload
    def cmd(self, *, func_name: str, kw_dict: dict) -> WebSocketPayload:
        """For client to order the command."""
        ...

    @overload
    def cmd(self, *, detail: dict) -> WebSocketPayload:
        """For server to send the result"""
        ...

    def cmd(self, **kwargs) -> WebSocketPayload:
        self.command = WSCommand.CMD
        match kwargs.keys():
            case ["detail"]:
                self.detail = kwargs["detail"]
            case ["func_name", "kw_dict"]:
                self.detail = {
                    "func_name": kwargs["func_name"],
                    "kw_dict": kwargs["kw_dict"],
                }
        return self

    async def send_ws(self, ws: WebSocket) -> None:
        await ws.send_bytes(self.as_bytes)
