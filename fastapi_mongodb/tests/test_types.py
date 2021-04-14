import unittest.mock

from fastapi_mongodb.helpers import AsyncTestCase
from fastapi_mongodb.types import OID


class TestOID(AsyncTestCase):
    def setUp(self) -> None:
        self.type_class = OID

    def test__modify_schema__(self):
        field_schema_mock = unittest.mock.MagicMock()

        self.type_class.__modify_schema__(field_schema=field_schema_mock)

        field_schema_mock.update.assert_called_once_with(
            pattern="^[a-f0-9]{24}$",
            example="5f5cf6f50cde9ec07786b294",
            title="ObjectId",
            type="string",
        )

    def test_validate(self):
        value = self.faker.pystr()
        with self.assertRaises(ValueError) as exception_context:
            self.type_class.validate(v=value)

        self.assertEqual(
            f"'{value}' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string",
            str(exception_context.exception),
        )
