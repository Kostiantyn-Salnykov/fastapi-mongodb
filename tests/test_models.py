import datetime
import unittest.mock

import bson
import motor.motor_asyncio
import pytest

import fastapi_mongodb

pytestmark = [pytest.mark.asyncio]


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
        patcher.patch_obj(target="fastapi_mongodb.helpers.utc_now", return_value=expected_utc_now)
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


# TODO: Refactor this test class
class TestBaseActiveRecord:
    WARNING_MSG = "Document already deleted or has not been created yet!"

    @staticmethod
    def _check_empty_active_record(active_record: fastapi_mongodb.models.BaseActiveRecord):
        assert active_record.id is None
        assert active_record.oid is None
        assert active_record.generated_at is None
        assert isinstance(active_record, fastapi_mongodb.models.BaseActiveRecord)

    @staticmethod
    def _check_filled_active_record(active_record: fastapi_mongodb.models.BaseActiveRecord, oid: bson.ObjectId):
        assert active_record.id == str(oid)
        assert active_record.oid == oid
        assert isinstance(active_record.generated_at, datetime.datetime)
        assert isinstance(active_record, fastapi_mongodb.models.BaseActiveRecord)

    def test_properties(self, faker, repository, patcher):
        logger = patcher.patch_obj(target="fastapi_mongodb.simple_logger")
        oid = bson.ObjectId()
        active_record = fastapi_mongodb.models.BaseActiveRecord(document=faker.pydict(), repository=repository)

        self._check_empty_active_record(active_record=active_record)
        logger.warning.assert_has_calls(
            calls=[
                unittest.mock.call(msg=self.WARNING_MSG),
                unittest.mock.call(msg=self.WARNING_MSG),
                unittest.mock.call(msg=self.WARNING_MSG),
            ]
        )

        active_record._document["_id"] = oid

        self._check_filled_active_record(active_record=active_record, oid=oid)

    def test_get_collection(self, repository):
        active_record = fastapi_mongodb.models.BaseActiveRecord(document={}, repository=repository)

        collection = active_record.get_collection()

        assert isinstance(collection, motor.motor_asyncio.AsyncIOMotorCollection)
        assert collection.name == "test_col"

    def test_get_db(self, repository):
        active_record = fastapi_mongodb.models.BaseActiveRecord(document={}, repository=repository)

        db = active_record.get_db()

        assert isinstance(db, motor.motor_asyncio.AsyncIOMotorDatabase)
        assert db.name == "test_db"

    async def test_insert_create(self, faker, repository, mongodb_session):
        oid = bson.ObjectId()
        document = {"_id": oid} | faker.pydict(10, True, [str, int, float, bool])

        active_record = await fastapi_mongodb.models.BaseActiveRecord.insert(
            document=document, repository=repository, session=mongodb_session
        )

        self._check_filled_active_record(active_record=active_record, oid=oid)
        assert active_record._document == document

    async def test_update(self, faker, repository, mongodb_session):
        test_key, test_value = faker.pystr(), faker.pystr()
        new_test_value = faker.pystr()
        remove_key, remove_value = faker.pystr(), faker.pystr()
        document = {test_key: test_value, remove_key: remove_value}

        active_record = await fastapi_mongodb.models.BaseActiveRecord.insert(
            document=document, repository=repository, session=mongodb_session
        )

        assert active_record[test_key] == test_value
        assert active_record[remove_key] == remove_value

        active_record[test_key] = new_test_value
        del active_record[remove_key]
        new_active_record = await active_record.update(session=mongodb_session)

        assert active_record[test_key] == new_test_value
        assert remove_key not in active_record
        assert active_record == new_active_record

    async def test_read_empty(self, faker, repository, mongodb_session, patcher):
        logger = patcher.patch_obj(target="fastapi_mongodb.simple_logger")
        fake_oid = bson.ObjectId()
        empty_active_record = await fastapi_mongodb.models.BaseActiveRecord.read(
            query={"_id": fake_oid}, repository=repository, session=mongodb_session
        )

        self._check_empty_active_record(active_record=empty_active_record)
        logger.warning.assert_has_calls(
            calls=[
                unittest.mock.call(msg=self.WARNING_MSG),
                unittest.mock.call(msg=self.WARNING_MSG),
                unittest.mock.call(msg=self.WARNING_MSG),
            ]
        )

    async def test_read_filled(self, faker, repository, mongodb_session):
        oid = bson.ObjectId()
        document = {"_id": oid} | faker.pydict(10, True, [str, int, float, bool])
        active_record = await fastapi_mongodb.models.BaseActiveRecord.insert(
            document=document, repository=repository, session=mongodb_session
        )

        self._check_filled_active_record(active_record=active_record, oid=oid)

    async def test_delete(self, faker, repository, mongodb_session, patcher):
        logger = patcher.patch_obj(target="fastapi_mongodb.simple_logger")
        oid = bson.ObjectId()
        document = {"_id": oid} | faker.pydict(10, True, [str, int, float, bool])
        active_record = await fastapi_mongodb.models.BaseActiveRecord.insert(
            document=document, repository=repository, session=mongodb_session
        )

        deleted_active_record = await active_record.delete(session=mongodb_session)

        self._check_empty_active_record(active_record=deleted_active_record)
        logger.warning.assert_has_calls(
            calls=[
                unittest.mock.call(msg=self.WARNING_MSG),
                unittest.mock.call(msg=self.WARNING_MSG),
                unittest.mock.call(msg=self.WARNING_MSG),
            ]
        )

    async def test_reload_refresh_empty(self, faker, repository, mongodb_session, patcher):
        logger = patcher.patch_obj(target="fastapi_mongodb.simple_logger")
        empty_active_record = fastapi_mongodb.models.BaseActiveRecord(document={}, repository=repository)

        self._check_empty_active_record(active_record=empty_active_record)
        assert logger.warning.call_count == 3  # 3 logs from _check method
        logger.warning.assert_has_calls(
            calls=[
                unittest.mock.call(msg=self.WARNING_MSG),
                unittest.mock.call(msg=self.WARNING_MSG),
                unittest.mock.call(msg=self.WARNING_MSG),
            ]
        )

        new_empty_active_record = await empty_active_record.reload(session=mongodb_session)

        self._check_empty_active_record(active_record=new_empty_active_record)
        assert logger.warning.call_count == 7  # 3 earlier + 1 from reload and another 3 from _check method
