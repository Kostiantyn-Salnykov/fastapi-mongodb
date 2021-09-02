import bson
import motor.motor_asyncio
import pytest
import pymongo.results
import fastapi_mongodb.repositories

pytestmark = [pytest.mark.asyncio]


class TestBaseRepository:
    @pytest.fixture(scope="class")
    def repository(self, db_manager):
        return fastapi_mongodb.repositories.BaseRepository(
            db_manager=db_manager, db_name="test_db", col_name="test_col"
        )

    def test_properties(self, repository, db_manager):

        assert repository.db == db_manager.retrieve_database(name="test_db")
        assert isinstance(repository.db, motor.motor_asyncio.AsyncIOMotorDatabase)

        assert repository.col == repository.db["test_col"]
        assert isinstance(repository.col, motor.motor_asyncio.AsyncIOMotorCollection)

    @pytest.fixture()
    def document(self, faker):
        return {"_id": bson.ObjectId(), faker.pystr(): faker.pystr()}

    @pytest.fixture()
    def documents(self, faker):
        count = faker.pyint(min_value=2, max_value=6)
        return [{"_id": bson.ObjectId(), faker.pystr(): faker.pystr()} for _ in range(count)]

    def _check_update_one_result(self, update_result: pymongo.results.UpdateResult):
        assert isinstance(update_result, pymongo.results.UpdateResult)
        assert 1 == update_result.matched_count
        assert 1 == update_result.modified_count
        assert update_result.upserted_id is None
        assert update_result.acknowledged is True

    async def test_insert_one(self, repository, document, mongodb_session):
        insert_one_result = await repository.insert_one(document=document, session=mongodb_session)

        assert isinstance(insert_one_result, pymongo.results.InsertOneResult)
        assert isinstance(insert_one_result.inserted_id, bson.ObjectId)
        assert insert_one_result.acknowledged is True

        inserted_document = await repository.find_one(query={"_id": document["_id"]}, session=mongodb_session)

        assert document == inserted_document

    async def test_insert_many(self, repository, documents, mongodb_session):
        ids_list = [document["_id"] for document in documents]
        insert_many_result = await repository.insert_many(documents=documents, session=mongodb_session)

        assert isinstance(insert_many_result, pymongo.results.InsertManyResult)
        assert ids_list == insert_many_result.inserted_ids
        assert insert_many_result.acknowledged is True

        cursor = await repository.find(query={"_id": {"$in": ids_list}}, session=mongodb_session)

        assert documents == [document async for document in cursor]

    async def test_replace_one(self, repository, faker, mongodb_session):
        old_data_key, new_data_key = faker.pystr(), faker.pystr()
        old_document = {"_id": bson.ObjectId(), old_data_key: faker.pystr()}
        await repository.insert_one(document=old_document, session=mongodb_session)

        new_document = {new_data_key: faker.pystr()}

        replace_one_result = await repository.replace_one(
            query={"_id": old_document["_id"]}, replacement=new_document, session=mongodb_session
        )

        self._check_update_one_result(update_result=replace_one_result)

        updated_old_document = await repository.find_one(query={"_id": old_document["_id"]}, session=mongodb_session)

        assert old_document["_id"] == updated_old_document["_id"]  # check _id field not changed
        assert new_document[new_data_key] == updated_old_document[new_data_key]

    async def test_update_one(self, repository, faker, mongodb_session):
        old_data_key, new_data_value = faker.pystr(), faker.pystr()

        old_document = {"_id": bson.ObjectId(), old_data_key: faker.pystr()}
        await repository.insert_one(document=old_document, session=mongodb_session)

        update_one_result = await repository.update_one(
            query={"_id": old_document["_id"]}, update={"$set": {old_data_key: new_data_value}}, session=mongodb_session
        )

        self._check_update_one_result(update_result=update_one_result)

        updated_old_document = await repository.find_one(query={"_id": old_document["_id"]}, session=mongodb_session)

        assert old_document["_id"] == updated_old_document["_id"]
        assert new_data_value == updated_old_document[old_data_key]

    async def test_update_many(self, repository, faker, mongodb_session):
        old_key, old_value, new_value = (faker.pystr(), faker.pystr(), faker.pystr())
        documents = [
            {"_id": bson.ObjectId(), old_key: old_value},
            {"_id": bson.ObjectId(), old_key: old_value},
        ]
        ids_list = [document["_id"] for document in documents]
        expected_documents = [
            {"_id": documents[0]["_id"], old_key: new_value},
            {"_id": documents[1]["_id"], old_key: new_value},
        ]
        await repository.insert_many(documents=documents, session=mongodb_session)

        update_many_result = await repository.update_many(
            query={"_id": {"$in": ids_list}}, update={"$set": {old_key: new_value}}, session=mongodb_session
        )

        assert isinstance(update_many_result, pymongo.results.UpdateResult)
        assert 2 == update_many_result.matched_count
        assert 2 == update_many_result.modified_count
        assert update_many_result.upserted_id is None
        assert update_many_result.acknowledged is True

        find_result = await repository.find(query={"_id": {"$in": ids_list}}, session=mongodb_session)

        assert expected_documents == [document async for document in find_result]

    async def test_delete_one(self, document, repository, mongodb_session):
        await repository.insert_one(document=document, session=mongodb_session)

        delete_result = await repository.delete_one(query={"_id": document["_id"]}, session=mongodb_session)

        assert isinstance(delete_result, pymongo.results.DeleteResult)
        assert 1 == delete_result.deleted_count
        assert delete_result.acknowledged is True

    async def test_delete_many(self, documents, repository, mongodb_session):
        ids_list = [document["_id"] for document in documents]
        await repository.insert_many(documents=documents, session=mongodb_session)

        delete_result = await repository.delete_many(query={"_id": {"$in": ids_list}}, session=mongodb_session)

        assert isinstance(delete_result, pymongo.results.DeleteResult)
        assert delete_result.deleted_count == len(documents)
        assert delete_result.acknowledged is True

    async def test_find(self, documents, repository, mongodb_session):
        ids_list = [document["_id"] for document in documents]
        await repository.insert_many(documents=documents, session=mongodb_session)

        find_result = await repository.find(query={"_id": {"$in": ids_list}}, session=mongodb_session)

        assert documents == [document async for document in find_result]

    async def test_find_one(self, document, repository, mongodb_session):
        await repository.insert_one(document=document, session=mongodb_session)

        find_one_result = await repository.find_one(query={"_id": document["_id"]}, session=mongodb_session)

        assert document == find_one_result

    async def test_find_one_and_delete(self, document, repository, mongodb_session):
        await repository.insert_one(document=document, session=mongodb_session)

        deleted_document = await repository.find_one_and_delete(query={"_id": document["_id"]}, session=mongodb_session)

        assert document == deleted_document

    async def test_find_one_and_replace(self, repository, faker, mongodb_session):
        new_key = faker.pystr()
        document = {"_id": bson.ObjectId(), faker.pystr(): faker.pystr()}
        replacement = {new_key: faker.pystr()}
        replaced_document = {"_id": document["_id"], new_key: replacement[new_key]}
        await repository.insert_one(document=document)
        query = {"_id": document["_id"]}

        result = await repository.find_one_and_replace(query=query, replacement=replacement)

        assert result == replaced_document

    async def test_find_one_and_update(self, repository, faker, mongodb_session):
        old_data_key, new_data_value = faker.pystr(), faker.pystr()

        old_document = {"_id": bson.ObjectId(), old_data_key: faker.pystr()}
        updated_document = {"_id": old_document["_id"], old_data_key: new_data_value}
        await repository.insert_one(document=old_document)

        find_one_and_update_result = await repository.find_one_and_update(
            query={"_id": old_document["_id"]},
            update={"$set": {old_data_key: new_data_value}},
        )

        assert updated_document == find_one_and_update_result

    async def test_count_documents(self, documents, repository, mongodb_session):
        await repository.insert_many(documents=documents, session=mongodb_session)
        ids_list = [document["_id"] for document in documents]

        result = await repository.count_documents(query={"_id": {"$in": ids_list}}, session=mongodb_session)

        assert len(documents) == result

    async def test_estimated_document_count(self, documents, repository, mongodb_session):
        await repository.delete_many(query={}, session=mongodb_session)
        await repository.insert_many(documents=documents, session=mongodb_session)

        result = await repository.estimated_document_count()

        assert len(documents) == result

    async def test_aggregate(self, documents, repository, mongodb_session):
        await repository.insert_many(documents=documents, session=mongodb_session)
        ids_list = [document["_id"] for document in documents]
        match_stage = {"$match": {"_id": {"$in": ids_list}}}

        cursor = await repository.aggregate(pipeline=[match_stage], session=mongodb_session)

        assert documents == [document async for document in cursor]

    async def test_bulk_write(self, repository, faker, mongodb_session):
        _id, field_name, expected_count = bson.ObjectId(), faker.pystr(), 1
        _check_attrs_list = [
            "deleted_count",
            "inserted_count",
            "matched_count",
            "modified_count",
            "upserted_count",
        ]
        operations = [
            pymongo.operations.UpdateOne(
                filter={"_id": _id},
                update={"$set": {field_name: faker.pystr()}},
                upsert=True,
            ),
            pymongo.operations.InsertOne(document={"_id": bson.ObjectId(), field_name: faker.pystr()}),
            pymongo.operations.UpdateOne(filter={"_id": _id}, update={"$set": {field_name: faker.pystr()}}),
            pymongo.operations.DeleteOne(filter={"_id": _id}),
        ]

        result = await repository.bulk_write(operations=operations, session=mongodb_session)

        assert isinstance(result, pymongo.results.BulkWriteResult)
        assert result.acknowledged is True
        assert _id in result.upserted_ids.values()
        for attr in _check_attrs_list:
            assert expected_count == getattr(result, attr)

    async def test_watch(self, document, repository, mongodb_session):
        pipeline = [{"$match": {"operationType": "insert"}}]
        change_stream_1 = await repository.watch(pipeline=pipeline, session=mongodb_session)
        nothing_yet = await change_stream_1.try_next()
        assert nothing_yet is None
        await repository.insert_one(document=document, session=mongodb_session)

        change_stream_2 = await repository.watch(
            pipeline=pipeline, resume_after=change_stream_1.resume_token, session=mongodb_session
        )
        streamed_document = await change_stream_2.try_next()

        assert document == streamed_document["fullDocument"]
