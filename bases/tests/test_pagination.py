import bases


class TestLimitOffsetPagination(bases.helpers.AsyncTestCaseWithPathing):
    def setUp(self) -> None:
        self.pagination_instance = bases.pagination.LimitOffsetPagination()

    def test__call__default(self):
        default_limit = bases.config.common_settings.PAGINATION_DEFAULT_LIMIT
        default_offset = bases.config.common_settings.PAGINATION_DEFAULT_OFFSET

        result = self.pagination_instance(limit=default_limit, offset=default_offset)

        self.assertIsInstance(result, bases.pagination.Paginator)
        self.assertEqual(default_limit, result.limit)
        self.assertEqual(default_offset, result.skip)

    def test__call__custom(self):
        custom_limit = self.faker.pyint(
            min_value=bases.config.common_settings.PAGINATION_MIN_LIMIT,
            max_value=bases.config.common_settings.PAGINATION_MAX_LIMIT,
        )
        custom_offset = self.faker.pyint(min_value=bases.config.common_settings.PAGINATION_MIN_OFFSET)

        result = self.pagination_instance(offset=custom_offset, limit=custom_limit)

        self.assertIsInstance(result, bases.pagination.Paginator)
        self.assertEqual(custom_limit, result.limit)
        self.assertEqual(custom_offset, result.skip)
