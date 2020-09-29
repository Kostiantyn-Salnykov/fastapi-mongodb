import asyncio
import functools
import unittest
import unittest.mock
import typing


class MakeAsync:
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))

        return wrapper


class AsyncCaseWithPatching(unittest.IsolatedAsyncioTestCase):
    def __setup_cleanup_and_get_mock(self, patcher):
        mock_instance = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_instance

    def create_patch(
        self, target, **kwargs
    ) -> typing.Union[unittest.mock.Mock, unittest.mock.MagicMock, unittest.mock.AsyncMock]:
        patcher = unittest.mock.patch(target=target, **kwargs)
        return self.__setup_cleanup_and_get_mock(patcher=patcher)

    def patch_obj(
        self, target, attribute, **kwargs
    ) -> typing.Union[unittest.mock.Mock, unittest.mock.MagicMock, unittest.mock.AsyncMock]:
        patcher = unittest.mock.patch.object(target=target, attribute=attribute, **kwargs)
        return self.__setup_cleanup_and_get_mock(patcher=patcher)

    def patch_property(
        self, target, attribute, return_value, **kwargs
    ) -> typing.Union[unittest.mock.Mock, unittest.mock.MagicMock, unittest.mock.AsyncMock]:
        patcher = unittest.mock.patch.object(
            target=target, attribute=attribute, new=unittest.mock.PropertyMock(return_value=return_value), **kwargs
        )
        return self.__setup_cleanup_and_get_mock(patcher=patcher)

    @staticmethod
    def create_async_iter_mock(return_value: typing.Iterable) -> unittest.mock.AsyncMock:
        async_mock = unittest.mock.AsyncMock()
        async_mock.__aiter__.return_value = return_value
        return async_mock

    def create_async_context_manager_mock(self):
        class AsyncContextManager:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                """exit from content manager"""

        return unittest.mock.AsyncMock(new=AsyncContextManager)
