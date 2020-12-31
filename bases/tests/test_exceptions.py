import fastapi

import bases


class TestPermissionException(bases.helpers.AsyncTestCaseWithPathing):
    def test__init__default(self):
        exception = bases.exceptions.PermissionException()

        self.assertEqual("You aren't authorized to make this action.", exception.detail)
        self.assertEqual(fastapi.status.HTTP_403_FORBIDDEN, exception.status_code)

    def test__init__custom(self):
        detail = self.faker.pystr()
        exception = bases.exceptions.PermissionException(detail=detail)

        self.assertEqual(detail, exception.detail)
        self.assertEqual(fastapi.status.HTTP_403_FORBIDDEN, exception.status_code)


class TestRepositoryException(bases.helpers.AsyncTestCaseWithPathing):
    def test__init___default(self):
        exception = bases.exceptions.RepositoryException()

        self.assertEqual("Repository exception.", exception.detail)
        self.assertEqual(fastapi.status.HTTP_400_BAD_REQUEST, exception.status_code)

    def test__init__custom(self):
        detail = self.faker.pystr()
        exception = bases.exceptions.RepositoryException(detail=detail)

        self.assertEqual(detail, exception.detail)
        self.assertEqual(fastapi.status.HTTP_400_BAD_REQUEST, exception.status_code)
