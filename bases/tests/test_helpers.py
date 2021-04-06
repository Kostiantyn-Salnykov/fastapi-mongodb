import datetime
import unittest.mock
import zoneinfo

import faker

from bases.helpers import AsyncTestCase, MakeAsync, as_utc, get_utc_timezone, utc_now


class TestMakeAsync(AsyncTestCase):
    def test__call__(self):
        test_args = self.faker.pytuple()
        test_kwargs = self.faker.pydict()
        expected_result = (test_args, test_kwargs)

        @MakeAsync()
        async def test_func(*args, **kwargs):
            return args, kwargs

        result = test_func(*test_args, **test_kwargs)

        self.assertEqual(expected_result, result)


class TestPatchingTestMixin(AsyncTestCase):
    class TestClass:
        test_attr = "TEST_ATTR"

        @property
        def test_property(self):
            return "TEST_PROPERTY"

    def test_faker(self):
        self.assertIsInstance(AsyncTestCase.faker, faker.Faker)

    def test_patch_property(self):
        expected_result = self.faker.pystr()
        self.assertNotEqual(expected_result, self.TestClass.test_property)

        self.patch_property(
            target=self.TestClass,
            attribute="test_property",
            return_value=expected_result,
        )

        self.assertEqual(expected_result, self.TestClass.test_property)

    def test_patch_obj(self):
        expected_result = self.faker.pystr()
        self.assertNotEqual(expected_result, self.TestClass.test_attr)

        self.patch_obj(target=self.TestClass, attribute="test_attr", new=expected_result)

        self.assertEqual(expected_result, self.TestClass.test_attr)

    async def test_create_async_iter_mock(self):
        expected_iterable = self.faker.pylist()

        result = [value async for value in self.create_async_iter_mock(return_value=expected_iterable)]

        self.assertEqual(expected_iterable, result)

    async def test_create_async_context_manager(self):
        async with self.create_async_context_manager_mock() as acm:
            self.assertIsInstance(acm, unittest.mock.AsyncMock)


class TestGetUTCTimezone(AsyncTestCase):
    def test_get_utc_timezone(self):
        result = get_utc_timezone()

        self.assertIsInstance(result, zoneinfo.ZoneInfo)
        self.assertEqual(result.key, "UTC")


class TestUTCNow(AsyncTestCase):
    def test_utc_now(self):
        expected_result = datetime.datetime.now(tz=zoneinfo.ZoneInfo("UTC"))
        datetime_mock = self.create_patch(target="bases.helpers.datetime.datetime")
        datetime_mock.now.return_value = expected_result

        result = utc_now()

        datetime_mock.now.assert_called_once_with(tz=get_utc_timezone())
        self.assertEqual(expected_result, result)


class TestAsUTC(AsyncTestCase):
    def test_as_utc(self):
        timezone_info = zoneinfo.ZoneInfo(key=self.faker.timezone())
        date_time: datetime.datetime = self.faker.date_time(tzinfo=timezone_info)
        expected_result = date_time.astimezone(tz=zoneinfo.ZoneInfo(key="UTC"))

        result = as_utc(date_time=date_time)

        self.assertEqual(expected_result, result)
