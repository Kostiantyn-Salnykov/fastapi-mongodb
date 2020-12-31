import datetime

import bson

import bases


class TestBaseMongoDBModel(bases.helpers.AsyncTestCaseWithPathing):
    class TestCreatedUpdatedModel(bases.models.BaseMongoDBModel, bases.models.BaseCreatedUpdatedModel):
        test: str

    class TestModel(bases.models.BaseMongoDBModel):
        test: str

    def setUp(self) -> None:
        self.model_class = bases.models.BaseMongoDBModel

    def test_from_db_default(self):
        data = {"_id": bson.ObjectId()}

        result = self.model_class.from_db(data=data)

        self.assertEqual(data["_id"], result.id)

    def test_from_db_none(self):
        data = None

        result = self.model_class.from_db(data=data)

        self.assertIsNone(result)

    def test_from_db_no_id(self):
        data = {self.faker.pystr(): self.faker.pystr()}

        result = self.model_class.from_db(data=data)

        self.assertEqual(self.model_class(id=None), result)

    def test_to_db(self):
        expected_object_id = bson.ObjectId()
        object_id_mock = self.patch_obj(target=bson, attribute="ObjectId", return_value=expected_object_id)
        expected_utc_now = datetime.datetime.utcnow()
        datetime_mock = self.create_patch(target="bases.models.datetime")
        datetime_mock.datetime.utcnow.return_value = expected_utc_now
        model = self.TestCreatedUpdatedModel(test=self.faker.pystr())

        result = model.to_db()

        object_id_mock.assert_called_once()
        self.assertEqual(expected_object_id, result["_id"])
        self.assertEqual(expected_object_id.generation_time.replace(tzinfo=None), result["created_datetime"])
        self.assertEqual(expected_utc_now, result["updated_datetime"])
        self.assertEqual(model.test, result["test"])

    def test_to_db_from_db_flow(self):
        expected_object_id = bson.ObjectId()
        self.patch_obj(target=bson, attribute="ObjectId", return_value=expected_object_id)
        to_db_data = {"test": self.faker.pystr()}
        expected_result = {"_id": expected_object_id} | to_db_data

        to_db_result = self.TestModel(**to_db_data).to_db()
        from_db_result = self.TestModel.from_db(data=to_db_result).to_db()

        self.assertEqual(expected_result, from_db_result)

    def test_to_db_from_db_flow_by_alias_false(self):
        expected_object_id = bson.ObjectId()
        to_db_data = {"test": self.faker.pystr(), "id": expected_object_id}
        expected_result = {"_id": expected_object_id} | to_db_data

        to_db_result = self.TestModel(**to_db_data).to_db(by_alias=False)
        from_db_result = self.TestModel.from_db(data=to_db_result).to_db(by_alias=False)

        expected_result.pop("id")
        self.assertEqual(expected_result, from_db_result)
