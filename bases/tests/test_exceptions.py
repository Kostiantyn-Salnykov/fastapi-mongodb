import fastapi

from bases.exceptions import PermissionException, RepositoryException
from bases.helpers import AsyncTestCase


class TestPermissionException(AsyncTestCase):
    def test__init__default(self):
        exception = PermissionException()

        self.assertEqual("You aren't authorized to make this action.", exception.detail)
        self.assertEqual(fastapi.status.HTTP_403_FORBIDDEN, exception.status_code)

    def test__init__custom(self):
        detail = self.faker.pystr()
        exception = PermissionException(detail=detail)

        self.assertEqual(detail, exception.detail)
        self.assertEqual(fastapi.status.HTTP_403_FORBIDDEN, exception.status_code)


class TestRepositoryException(AsyncTestCase):
    def test__init___default(self):
        exception = RepositoryException()

        self.assertEqual("Repository exception.", exception.detail)
        self.assertEqual(fastapi.status.HTTP_400_BAD_REQUEST, exception.status_code)

    def test__init__custom(self):
        detail = self.faker.pystr()
        exception = RepositoryException(detail=detail)

        self.assertEqual(detail, exception.detail)
        self.assertEqual(fastapi.status.HTTP_400_BAD_REQUEST, exception.status_code)
