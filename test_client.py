import asyncio as aio

from aiounittest import AsyncTestCase
from pprint import pprint as print

from client.network import Client, Credential


class TestClientNetwork(AsyncTestCase):
    async def setUp(self):
        self.server = await aio.create_subprocess_shell('uvicorn server:app --reload')
        self.client = Client()

    async def test_register(self):
        p_info = await self.client.register(
            username='test_register',
            password='123456',
        )
        print(p_info)
