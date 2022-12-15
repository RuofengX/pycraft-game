from dataclasses import dataclass
from typing import Any, Dict, NoReturn, Optional

from aiohttp import ClientSession

from pyworld.datamodels.function_call import ServerRtn

# from pyworld.datamodels.websockets import WSPayload


PROTOCOL = 'https:'
BASE_URL = '//localhost:8000'
INFO_PATH = '/player'
REGISTER_PATH = '/register'
CTRL_GET_PROPERTY_PATH = '/ctrl/get-property'
CTRL_GET_METHOD_PATH = '/ctrl/get-method'
CTRL_CALL_PATH = '/ctrl/call'
CTRL_STREAM_PATH = '/ctrl/stream'


@dataclass
class Credential():
    username: Optional[str] = None
    password: Optional[str] = None


class Client(ClientSession):
    """Use async with Client() to Open new session."""

    def __init__(
        self,
        cred: Optional[Credential] = None,
    ) -> None:
        if cred is not None:
            self.username: Optional[str] = cred.username
            self.password: Optional[str] = cred.password

    async def register(self, username, password) -> NoReturn | Dict[str, Any]:
        uri = f'{PROTOCOL}{BASE_URL}{REGISTER_PATH}'\
            '?username={username}&password={password}'
        async with self.get(url=uri) as response:
            assert response.status == 200, response.status
            return ServerRtn(
                **(await response.json())
            ).dict()
