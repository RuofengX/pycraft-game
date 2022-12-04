from __future__ import annotations

import base64
import json
import pickle
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Optional, cast, Generic, TypeVar

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

    def get_entity_property(self, ent: ControlMixin) -> str:
        rtn = self.get_raw(ent)
        self[ent.uuid] = rtn
        return json.dumps(rtn)

    def get_diff_property(self, ent: ControlMixin) -> str:
        ent_id: int = ent.uuid
        raw: dict = self.get_raw(ent)
        if ent_id not in self:
            self[ent_id] = {}
        diff: list = list(dictdiffer.diff(self[ent.uuid], raw))
        self[ent.uuid] = raw
        return json.dumps({"diff": diff})


class EncodeMode(Enum):
    B64_PICKLE_BYTES = 0x0
    JSON = 0x1

    def __len__(self):
        return 2


_Cls = TypeVar('_Cls')


@dataclass(init=True, repr=False)
class Payload(Generic[_Cls]):
    """
    Receive data container.

    # TODO: Use pydantic.BaseModel to do regulation
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

    @property
    def length(self):
        return len(self.as_bytes)

    @staticmethod
    def from_dict(d: dict) -> Payload:
        rtn: Payload = Payload()
        for key in d:
            setattr(rtn, key, d[key])
        return rtn

    @classmethod
    def from_bytes(cls: _Cls, b: bytes, mode: EncodeMode | str) -> _Cls:
        if type(mode) == EncodeMode:
            pass
        else:
            try:
                mode = EncodeMode(mode)
            except TypeError as e:
                raise TypeError(f"Unsupported EncodeMode str.[{str(e)}]")

        if mode is EncodeMode.B64_PICKLE_BYTES:
            rtn = pickle.loads(base64.b64decode(b))
        elif mode is EncodeMode.JSON:
            rtn = Payload.from_dict(json.loads(b.decode("utf8")))

        cast(cls, rtn)  # type: ignore
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
    A bried protocol instruments:

    STAGE
    0. Just a simple States Machine

    INIT
    1. client send the GET request with creds to ws uri,
    2. a ws created,
    LOGIN
    2.1. server check the creds, if invalid -> (CLOSE, {})
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
    CLOSE = 0x01  # S: creds is invalid
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
        detail: infomation body, mostly used by server,
            used to return the info that client asked.
    """

    default_encode = field(default=EncodeMode.JSON, init=False)

    stage: WebSocketStage = field(default=WebSocketStage.UNKNOWN)
    command: WSCommand = WSCommand.PING
    detail: Dict[str, Any] = {}

    async def send(self, ws: WebSocket) -> None:
        await ws.send_bytes(
            self.as_bytes
        )
        return

    @staticmethod
    async def from_read_ws(ws: WebSocket) -> WebSocketPayload:
        return WebSocketPayload.from_bytes(
            await ws.receive_bytes(), mode=EncodeMode.JSON
        )
