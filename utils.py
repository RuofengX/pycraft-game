from __future__ import annotations

import base64
import binascii
import json
import pickle
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, NoReturn

import dictdiffer
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


@dataclass(init=True, repr=False)
class Payload:
    """
     Receive data container.
    """

    @staticmethod
    def from_dict(d: dict) -> Payload:
        rtn: Payload = Payload()
        for key in d:
            setattr(rtn, key, d[key])
        return rtn

    @staticmethod
    def from_bytes(b: bytes) -> Payload:
        rtn: Any = pickle.loads(b)
        assert isinstance(rtn, Payload)
        return rtn


class WebSocketStage(Enum):
    UNKNOWN = -1
    INIT = 0
    LOGIN = 1
    LOOP = 2
    CLIENT_PREPARE = 3
    CLIENT_SEND = 4
    SERVER_PREPARE = 5
    SERVER_SEND = 6


class WebSocketPayload(Payload):
    stage: WebSocketStage = WebSocketStage.UNKNOWN
    detail: Dict[str, Any] = field(default_factory=dict)

    async def send(self, ws: WebSocket) -> None:
        await ws.send_bytes(base64.b64encode(pickle.dumps(self)))

    @staticmethod
    def from_bytes(b: bytes) -> WebSocketPayload | NoReturn:
        """Raise ValueError"""
        try:
            rtn: Any = pickle.loads(base64.b64decode(b))
            assert isinstance(rtn, WebSocketPayload), "Receiving data error."
            return rtn
        except pickle.UnpicklingError:
            raise ValueError("Error when unpickling objects.")
        except binascii.Error:
            raise ValueError("Error when decode use base64.")

    @staticmethod
    async def from_ws(ws: WebSocket) -> WebSocketPayload | NoReturn:
        """Raise WebSocketDisconnect"""
        return WebSocketPayload.from_bytes(await ws.receive_bytes())


if __name__ == "__main__":
    pass
