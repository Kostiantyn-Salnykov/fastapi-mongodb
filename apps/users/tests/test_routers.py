import fastapi
import httpx

from bases.helpers import AsyncTestCase


class TestUsersRouter(AsyncTestCase):
    def setUp(self) -> None:
        super().setUp()

    async def test_get_users_not_authorized(self):
        response: httpx.Response = await self.async_client.get(url="/users/")

        self.assertEqual(fastapi.status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({"detail": "You aren't authorized to make this action."}, response.json())
