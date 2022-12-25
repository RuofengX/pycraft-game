import base64
import pickle
from dataclasses import dataclass
from typing import Any, NoReturn, Optional, Self, Type, TypeVar, cast, overload

from aiohttp import ClientSession

from pyworld.datamodels.status_code import CallStatus
from pyworld.player import Player

# from pyworld.datamodels.websockets import WSPayload


PROTOCOL = "https:"
BASE_URL = "//localhost:8000"
INFO_PATH = "/player"
REGISTER_PATH = "/register"
CTRL_LIST_PROPERTY_PATH = "/ctrl/list-property"
CTRL_GET_PROPERTY_PATH = "/ctrl/get-property"
CTRL_GET_METHOD_PATH = "/ctrl/get-method"
CTRL_CALL_PATH = "/ctrl/call"
CTRL_STREAM_PATH = "/ctrl/stream"


@dataclass
class Credential:
    username: Optional[str] = None
    password: Optional[str] = None


T = TypeVar("T", bound=Any)


class Client(ClientSession):
    """Use async with Client() to Open new session."""

    def __init__(
        self,
        cred: Optional[Credential] = None,
    ) -> None:
        if cred is not None:
            self.username: Optional[str] = cred.username
            self.password: Optional[str] = cred.password

        self.player: Optional[Player] = None

    @overload
    @staticmethod
    def decode(b: str | bytes) -> Any:
        ...

    @overload
    @staticmethod
    def decode(b: str | bytes, expect_type: Type[T]) -> T:
        ...

    @staticmethod
    def decode(b: str | bytes, expect_type: Optional[Type[T]] = None) -> T | Any:
        if isinstance(b, str):
            b = b.encode('utf-8')
        rtn = pickle.loads(base64.b64decode(b))
        if expect_type is not None:
            return cast(expect_type, rtn)
        else:
            return rtn

    @classmethod
    async def register(cls, username, password) -> Self | NoReturn:
        self = cls(cred=Credential(username, password))

        uri = (
            f"{PROTOCOL}{BASE_URL}{REGISTER_PATH}"
            "?username={username}&password={password}"
        )

        async with self.get(url=uri) as response:
            assert response.status == 200
            payload = await response.json()

        assert payload["status"] == CallStatus.SUCCESS
        data = payload["detail"]
        self.player = Client.decode(data, Player)

        return self

    @classmethod
    def from_bytes(cls, b: bytes) -> Self:
        self = cls()
        self.player = Client.decode(b, Player)
        return self

