import unittest.mock

import bases
import faker


class TestMakeAsync(bases.helpers.AsyncTestCaseWithPathing):
    def test__call__(self):
        test_args = self.faker.pytuple()
        test_kwargs = self.faker.pydict()
        expected_result = (test_args, test_kwargs)

        @bases.helpers.MakeAsync()
        async def test_func(*args, **kwargs):
            return args, kwargs

        result = test_func(*test_args, **test_kwargs)

        self.assertEqual(expected_result, result)


class TestAsyncTestCaseWithPathing(bases.helpers.AsyncTestCaseWithPathing):
    class TestClass:
        test_attr = "TEST_ATTR"

        @property
        def test_property(self):
            return "TEST_PROPERTY"

    def test_faker(self):
        self.assertIsInstance(bases.helpers.AsyncTestCaseWithPathing.faker, faker.Faker)

    def test_patch_property(self):
        expected_result = self.faker.pystr()
        self.assertNotEqual(expected_result, self.TestClass.test_property)

        self.patch_property(target=self.TestClass, attribute="test_property", return_value=expected_result)

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
