import unittest.mock

import pytest
from bson import ObjectId

from fastapi_mongodb.types import OID


class TestOID:
    @classmethod
    def setup_class(cls) -> None:
        cls.type_class = OID

    def test__modify_schema__(self):
        field_schema_mock = unittest.mock.MagicMock()

        self.type_class.__modify_schema__(field_schema=field_schema_mock)

        field_schema_mock.update.assert_called_once_with(
            pattern="^[a-f0-9]{24}$",
            example="5f5cf6f50cde9ec07786b294",
            title="ObjectId",
            type="string",
        )

    def test_validate_error(self, faker):
        value = faker.pystr()

        with pytest.raises(ValueError) as exception_context:
            self.type_class.validate(v=value)

        assert f"'{value}' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string" == str(
            exception_context.value
        )

    def test_validate_success(self, faker):
        object_id = ObjectId()

        result = self.type_class.validate(v=object_id)

        assert result == object_id
