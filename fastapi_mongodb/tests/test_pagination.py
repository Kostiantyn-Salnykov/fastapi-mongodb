from fastapi_mongodb.config import bases_settings
from fastapi_mongodb.helpers import AsyncTestCase
from fastapi_mongodb.pagination import LimitOffsetPagination, Paginator


class TestLimitOffsetPagination(AsyncTestCase):
    def setUp(self) -> None:
        self.pagination_instance = LimitOffsetPagination()

    def test__call__default(self):
        default_limit = bases_settings.PAGINATION_DEFAULT_LIMIT
        default_offset = bases_settings.PAGINATION_DEFAULT_OFFSET

        result = self.pagination_instance(limit=default_limit, offset=default_offset)

        self._extracted_from_test__call__custom_7(
            result, default_limit, default_offset
        )

    def test__call__custom(self):
        custom_limit = self.faker.pyint(
            min_value=bases_settings.PAGINATION_MIN_LIMIT,
            max_value=bases_settings.PAGINATION_MAX_LIMIT,
        )
        custom_offset = self.faker.pyint(min_value=bases_settings.PAGINATION_MIN_OFFSET)

        result = self.pagination_instance(offset=custom_offset, limit=custom_limit)

        self._extracted_from_test__call__custom_7(result, custom_limit, custom_offset)

    def _extracted_from_test__call__custom_7(self, result, arg1, arg2):
        self.assertIsInstance(result, Paginator)
        self.assertEqual(arg1, result.limit)
        self.assertEqual(arg2, result.skip)
