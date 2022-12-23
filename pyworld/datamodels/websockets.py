from __future__ import annotations

import base64
import json
import pickle
from enum import Enum
from typing import Any, Dict, Optional, overload, List, Self
from fastapi import WebSocket
from pydantic import BaseModel

from pyworld.datamodels.function_call import CallRequestModel, ExceptionModel
from pyworld.control import ControlResultModel


class EncodeMode(Enum):
    B64_PICKLE_BYTES = 0x0
    JSON = 0x1

    def __len__(self):
        return 2


class Payload(BaseModel):
    """
    Receive data container.

    # TODO: Test needed
    """

    default_encode: EncodeMode = EncodeMode.JSON

    @property
    def as_bytes(self, encode: Optional[EncodeMode] = None) -> bytes:
        if encode is None:
            encode = self.default_encode

        if encode is EncodeMode.B64_PICKLE_BYTES:
            return base64.b64encode(pickle.dumps(self.dict()))
        elif encode is EncodeMode.JSON:
            return str(self.dict()).encode("utf8")
        else:
            raise NotImplementedError("Unsupported encode.")

    @property
    def length(self) -> int:
        return len(self.as_bytes)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Payload:
        rtn: Payload = Payload()
        for key in d:
            setattr(rtn, key, d[key])
        return rtn

    @classmethod
    def from_bytes(
        cls, b: bytes, mode: EncodeMode | str
    ) -> Self:  # type: ignore[valid-type]
        # TODO: mypy do not recognize Self annotation
        if type(mode) == EncodeMode:
            pass
        else:
            try:
                mode = EncodeMode(mode)
            except TypeError as e:
                raise TypeError(f"Unsupported EncodeMode str.[{str(e)}]")

        rtn: Self  # type: ignore[valid-type]
        match mode:
            case EncodeMode.B64_PICKLE_BYTES:
                rtn = pickle.loads(base64.b64decode(b))
            case EncodeMode.JSON:
                rtn = Payload.from_dict(json.loads(b.decode("utf8")))
            case other:
                raise NotImplementedError(f"Unsupported EncodeMode: {str(other)}")

        return rtn


class WSStage(Enum):
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


class WSPayload(Payload):
    """
    Override: WebSocket use JSON to exchange data by force.
    Properties:
        stage: Record the stage for assert and debug use.
        command: the Command slot, mostly used by client, used to order the peer.
        detail: information body, mostly used by server,
            used to return the info that client asked.
    """

    stage: WSStage = WSStage.UNKNOWN
    command: WSCommand = WSCommand.PING
    detail: Dict[str, Any] = {}
    exception: Optional[ExceptionModel] = None

    default_encode: EncodeMode = EncodeMode.JSON

    @staticmethod
    async def from_read_ws(ws: WebSocket) -> WSPayload:
        return WSPayload.from_bytes(await ws.receive_bytes(), mode=EncodeMode.JSON)

    def ping(self, stage: WSStage) -> WSPayload:
        self.stage = stage
        self.command = WSCommand.PING
        self.detail = {}
        return self

    def close(
        self, stage: WSStage, reason: str, exception: Optional[Exception] = None
    ) -> WSPayload:
        self.stage = stage
        self.command = WSCommand.CLOSE
        self.detail = {
            "reason": reason,
        }
        if exception is not None:
            self.exception = ExceptionModel.from_exception(exception)
        return self

    def all(self, stage: WSStage, detail: Dict[str, Any]) -> WSPayload:
        self.stage = stage
        self.command = WSCommand.ALL
        self.detail = detail
        return self

    def diff(self, stage: WSStage, detail: Dict[str, List[Any]]) -> WSPayload:
        self.stage = stage
        self.command = WSCommand.DIFF
        self.detail = detail
        return self

    @overload
    def cmd(self, *, server_resp: ControlResultModel) -> WSPayload:
        """For server to send the result"""
        ...

    @overload
    def cmd(self, *, client_req: CallRequestModel) -> WSPayload:
        """For client to order the command."""
        ...

    def cmd(self, **kwargs) -> WSPayload:
        self.command = WSCommand.CMD
        k = list(kwargs.keys())[0]  # HACK: Use more pythonic way.
        v = list(kwargs.values())[0]
        match k:
            case ["server_resp"]:
                self.stage = WSStage.SERVER_PREPARE
                self.detail = v["detail"]
            case ["client_req"]:
                self.stage = WSStage.CLIENT_PREPARE
                patch: CallRequestModel = v["req_patch"]
                self.detail = patch.dict()
        return self

    async def send_ws(self, ws: WebSocket) -> None:
        await ws.send_bytes(self.as_bytes)
