import asyncio
import datetime
import functools
import time
import tracemalloc
import typing
import unittest
import unittest.mock
import zoneinfo

import faker
import motor.motor_asyncio
import pymongo

import bases
import settings

__all__ = ["MakeAsync", "AsyncTestCaseWithPathing", "MongoDBTestCase", "get_utc_timezone", "utc_now", "as_utc"]


class MakeAsync:
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))

        return wrapper


class AsyncTestCaseWithPathing(unittest.IsolatedAsyncioTestCase):
    faker = faker.Faker()

    def __setup_cleanup_and_get_mock(self, *, patcher):
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
            async def __aenter__(self):  # pragma: no cover
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                """exit from content manager"""

        return unittest.mock.AsyncMock(new=AsyncContextManager)


class MongoDBTestCase(AsyncTestCaseWithPathing):
    TEST_DB_NAME = settings.Settings.MONGO_TEST_DB_NAME

    @staticmethod
    def _get_client_for_test():
        return motor.motor_asyncio.AsyncIOMotorClient(settings.Settings.MONGO_TEST_URL)

    async def _remove_test_database(self):
        await bases.db.DBHandler.delete_database(name=self.TEST_DB_NAME)

    def setUp(self) -> None:
        super().setUp()
        self._mongo_client: pymongo.MongoClient = self._get_client_for_test()
        self.patch_obj(target=bases.db.DBHandler, attribute="retrieve_client", return_value=self._mongo_client)
        self.patch_obj(
            target=bases.db.DBHandler,
            attribute="retrieve_database",
            return_value=bases.db.DBHandler.retrieve_database(name=self.TEST_DB_NAME),
        )
        self.addAsyncCleanup(self._remove_test_database)
        self.addClassCleanup(self._mongo_client.close)


# TODO (Add dump to file and load from file) kost:
class BaseProfiler:
    def __init__(
        self,
        number_frames: int = None,
        clear_traces: bool = True,
        include_files: list[str] = None,
        exclude_files: list[str] = None,
        show_memory: bool = True,
    ):
        self.number_frames = number_frames
        self.clear_traces = clear_traces
        self.include_files = include_files if include_files else []
        self.exclude_files = exclude_files if exclude_files else []
        self.show_memory = show_memory
        self._start_time = None
        self._end_time = None

    def __call__(self, func):
        @functools.wraps(func)
        def decorated(*args, **kwargs):
            self._start_trace_malloc()
            self._start_time = time.time()
            result = func(*args, **kwargs)
            self._end_time = time.time()
            self._print_timing(name=func.__name__)
            self._end_trace_malloc()
            return result

        return decorated

    def __enter__(self):
        self._start_trace_malloc()
        self._start_time = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_time = time.time()
        self._print_timing(name="Code block")
        self._end_trace_malloc()

    def _start_trace_malloc(self):
        tracemalloc.start(self.number_frames) if self.number_frames else tracemalloc.start()

    def _end_trace_malloc(self):
        print("=== START SNAPSHOT ===")
        snapshot = tracemalloc.take_snapshot()
        snapshot = snapshot.filter_traces(filters=self._get_trace_malloc_filters())
        for stat in snapshot.statistics(key_type="lineno", cumulative=True):
            print(stat)
        if self.show_memory:
            size, peak = tracemalloc.get_traced_memory()
            snapshot_size = tracemalloc.get_tracemalloc_memory()
            print(
                f"❕size={self._bytes_to_megabytes(size=size)}, "
                f"❗peak={self._bytes_to_megabytes(size=peak)}, "
                f"💾snapshot_size={self._bytes_to_megabytes(size=snapshot_size)}"
            )
        if self.clear_traces:
            tracemalloc.clear_traces()
        print("=== END SNAPSHOT ===")

    def _get_trace_malloc_filters(self) -> list[typing.Union[tracemalloc.Filter, tracemalloc.DomainFilter]]:
        filters = []
        for file_name in self.include_files:
            filters.append(tracemalloc.Filter(inclusive=True, filename_pattern=file_name))
        for file_name in self.exclude_files:
            filters.append(tracemalloc.Filter(inclusive=False, filename_pattern=file_name))
        return filters

    @staticmethod
    def _bytes_to_megabytes(size: int, precision: int = 3):
        return f"{size / 1024.0 / 1024.0:.{precision}f} MB"

    def _print_timing(self, name: str, precision: int = 5):
        print(f"📊{name} ⏱: {self._end_time - self._start_time:.{precision}f} seconds")


@functools.lru_cache()
def get_utc_timezone() -> zoneinfo.ZoneInfo:
    try:
        import zoneinfo
        utc_tz = zoneinfo.ZoneInfo(key="UTC")
    except ImportError:  # pragma: no cover
        utc_tz = datetime.timezone.utc
    return utc_tz


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(tz=get_utc_timezone())


def as_utc(date_time: datetime.datetime) -> datetime.datetime:
    return date_time.astimezone(tz=get_utc_timezone())
