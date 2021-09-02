import datetime
import random
import zoneinfo

import fastapi_mongodb.helpers
from tests.conftest import Patcher


class TestHelpers:
    def test_get_utc_timezone(self):
        result = fastapi_mongodb.helpers.get_utc_timezone()

        assert result.key == "UTC"
        assert isinstance(result, zoneinfo.ZoneInfo)

    def test_utc_now(self, patcher: Patcher):
        expected_zoneinfo = zoneinfo.ZoneInfo("UTC")
        expected_now = datetime.datetime.now(tz=expected_zoneinfo)
        datetime_mock = patcher.patch(target="fastapi_mongodb.helpers.datetime.datetime")
        datetime_mock.now.return_value = expected_now

        result = fastapi_mongodb.helpers.utc_now()

        assert result == expected_now
        assert result.tzinfo == expected_zoneinfo

    def test_as_utc(self):
        tz = zoneinfo.ZoneInfo(key=random.choice(list(zoneinfo.available_timezones())))
        dt = datetime.datetime.now(tz=tz)

        result = fastapi_mongodb.helpers.as_utc(date_time=dt)

        assert result.tzinfo == fastapi_mongodb.helpers.get_utc_timezone()
        assert result.astimezone(tz=tz) == dt


class TestBaseProfiler:
    @classmethod
    def setup_class(cls):
        cls.base_profiler = fastapi_mongodb.helpers.BaseProfiler(include_files=["test_helpers.py"])

    def test_profiler_decorator(self):
        @self.base_profiler
        def something():
            return True

        something()

    def test_profiler_context_manager(self):
        def something_new():
            return False

        with self.base_profiler:
            something_new()
