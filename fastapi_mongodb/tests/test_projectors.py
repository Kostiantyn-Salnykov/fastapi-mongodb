import pydantic

from fastapi_mongodb.exceptions import HandlerException
from fastapi_mongodb.helpers import AsyncTestCase
from fastapi_mongodb.models import BaseDBModel
from fastapi_mongodb.projectors import BaseProjector


class TestBaseProjector(AsyncTestCase):
    class TestModel(BaseDBModel):
        test: str = pydantic.Field(alias="test_alias")

    def setUp(self) -> None:
        self.projector_instance = BaseProjector(model_class=self.TestModel)

    def test__call___error(self):
        with self.assertRaises(HandlerException) as exception_context:
            self.projector_instance(fields_show="test", fields_hide="test")

        self.assertEqual(
            "You can't add 'fieldsShow' and 'fieldsHide' together to Projector",
            str(exception_context.exception),
        )

    def test__call__(self):
        for fields_show, fields_hide in [("test", None), (None, "test")]:
            with self.subTest():
                result = self.projector_instance(fields_show=fields_show, fields_hide=fields_hide)
                self.assertIsInstance(result, BaseProjector)

    def test_to_db_empty(self):
        result = self.projector_instance(fields_show=None, fields_hide=None).to_db()

        self.assertIsNone(result)

    def test_to_db_show(self):
        key1, key2, key3 = self.faker.pystr(), self.faker.pystr(), "test"
        expected_result = {key1: True, key2: True, f"{key3}_alias": True}

        result = self.projector_instance(fields_show=f" {key1} , {key2} , {key3} ", fields_hide=None).to_db()

        self.assertEqual(expected_result, result)

    def test_to_db_hide(self):
        key1, key2, key3 = self.faker.pystr(), "_id", "test"
        expected_result = {key1: False, f"{key3}_alias": False}

        result = self.projector_instance(fields_show=None, fields_hide=f" {key1} , {key2} , {key3} , , ").to_db()

        self.assertEqual(expected_result, result)
