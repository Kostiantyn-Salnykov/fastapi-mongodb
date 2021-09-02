import bson
import pytest

import fastapi_mongodb.helpers
import fastapi_mongodb.models


class TestBaseDBModel:
    class MyCreatedUpdatedModel(fastapi_mongodb.models.BaseCreatedUpdatedModel):
        test: str

    class MyModel(fastapi_mongodb.models.BaseDBModel):
        test: str

    @classmethod
    def setup_class(cls):
        cls.model_class = fastapi_mongodb.models.BaseDBModel

    def test_from_db_default(self):
        data = {"_id": bson.ObjectId()}
        oid = data["_id"]

        result = self.model_class.from_db(data=data)

        assert oid == result.oid
        assert str(oid) == result.id

    def test_from_db_none(self):
        data = None

        result = self.model_class.from_db(data=data)

        assert result is None

    def test_from_db_no_id(self, faker):
        data = {faker.pystr(): faker.pystr()}

        result = self.model_class.from_db(data=data)

        assert self.model_class(id=None) == result

    def test_to_db(self, faker, monkeypatch, patcher):
        expected_object_id = bson.ObjectId()
        monkeypatch.setattr(target=bson, name="ObjectId", value=lambda *args, **kwargs: expected_object_id)
        expected_utc_now = fastapi_mongodb.helpers.utc_now()
        patcher.patch(target="fastapi_mongodb.helpers.utc_now", return_value=expected_utc_now)
        model = self.MyCreatedUpdatedModel(test=faker.pystr())

        result = model.to_db()

        assert expected_object_id == result["_id"]
        assert (
            expected_object_id.generation_time.replace(tzinfo=fastapi_mongodb.helpers.get_utc_timezone())
            == result["created_at"]
        )
        assert expected_utc_now == result["updated_at"]
        assert model.test, result["test"]

    def test_to_db_from_db_flow(self, monkeypatch: pytest.MonkeyPatch, faker):
        expected_object_id = bson.ObjectId()
        monkeypatch.setattr(target=bson, name="ObjectId", value=lambda *args, **kwargs: expected_object_id)
        to_db_data = {"test": faker.pystr()}
        expected_result = {"_id": expected_object_id} | to_db_data

        to_db_result = self.MyModel(**to_db_data).to_db()
        from_db_result = self.MyModel.from_db(data=to_db_result).to_db()

        assert expected_result == from_db_result

    def test_to_db_with_id(self, faker):
        oid = bson.ObjectId()

        to_db_result = self.MyModel(_id=oid, test=faker.pystr()).to_db()

        assert oid == to_db_result["_id"]


class TestBaseActiveRecord:
    pass
