from unittest.mock import MagicMock

import fastapi
import pymongo
from bson import ObjectId
from pymongo.results import InsertOneResult, InsertManyResult, DeleteResult, UpdateResult

import bases


class TestBaseRepositoryConfig(bases.helpers.AsyncTestCaseWithPathing):
    class BaseMongoDBModelMock(bases.models.BaseMongoDBModel):
        pass

    def setUp(self) -> None:
        self.base_repository_config_class = bases.repositories.BaseRepositoryConfig

    def test__init__(self):
        instance = self.base_repository_config_class(convert_to=self.BaseMongoDBModelMock)

        self.assertTrue(instance.convert)
        self.assertEqual(self.BaseMongoDBModelMock, instance.convert_to)
        self.assertTrue(instance.raise_not_found)

    def test__init__convert_to_none(self):
        with self.assertRaises(NotImplementedError) as exception_context:
            self.base_repository_config_class()

        self.assertEqual("Set 'convert_to' attribute or set 'convert' to False", str(exception_context.exception))

    def test__init__convert_to_invalid(self):
        with self.assertRaises(NotImplementedError) as exception_context:
            self.base_repository_config_class(convert_to=MagicMock())

        self.assertEqual(
            f"'convert_to' kwarg must be a subclass from '{bases.models.BaseMongoDBModel.__name__}'",
            str(exception_context.exception),
        )


class TestBaseRepository(bases.helpers.MongoDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.col_name = "TEST_COL"
        self.obj_name = "TEST_OBJ"
        self.repository_config = bases.repositories.BaseRepositoryConfig(convert=False)
        self.repository_class = bases.repositories.BaseRepository(
            col_name=self.col_name, obj_name=self.obj_name, repository_config=self.repository_config
        )

    def test_convert_one_result_disabled(self):
        result_dict = self.faker.pydict()

        result = self.repository_class.convert_one_result(result=result_dict)

        self.assertEqual(result_dict, result)

    def test_convert_one_result(self):
        result_dict = self.faker.pydict()
        repository_config_mock = MagicMock(convert=True)
        expected_result = repository_config_mock.convert_to.from_db(data=result_dict)
        repository_config_mock.reset_mock()

        result = self.repository_class.convert_one_result(result=result_dict, repository_config=repository_config_mock)

        repository_config_mock.convert_to.from_db.assert_called_once_with(data=result_dict)
        self.assertEqual(expected_result, result)

    async def test_convert_many_results_disabled(self):
        expected_result = self.faker.pylist()
        results_cursor_mock = self.create_async_iter_mock(return_value=expected_result)

        result = await self.repository_class.convert_many_results(results_cursor=results_cursor_mock)

        self.assertEqual(expected_result, result)

    async def test_convert_many_results(self):
        test_data_list = self.faker.pylist()
        results_cursor_mock = self.create_async_iter_mock(return_value=test_data_list)
        repository_config_mock = MagicMock(convert=True)
        expected_result = [
            repository_config_mock.convert_to.from_db(data=result) async for result in results_cursor_mock
        ]
        repository_config_mock.reset_mock()

        result = await self.repository_class.convert_many_results(
            results_cursor=results_cursor_mock, repository_config=repository_config_mock
        )

        self.assertEqual(expected_result, result)

    def test__raise_not_found(self):
        result_dict = self.faker.pydict()
        repository_config_mock = MagicMock(raise_not_found=True)

        result = self.repository_class._raise_not_found(result=result_dict, repository_config=repository_config_mock)

        self.assertIsNone(result)

    def test__raise_not_found_disabled(self):
        query_result = None
        repository_config_mock = MagicMock(raise_not_found=False)

        result = self.repository_class._raise_not_found(result=query_result, repository_config=repository_config_mock)

        self.assertIsNone(result)

    def test__raise_not_found_enabled(self):
        query_result = None
        repository_config_mock = MagicMock(raise_not_found=True)

        with self.assertRaises(bases.exceptions.RepositoryException) as exception_context:
            self.repository_class._raise_not_found(result=query_result, repository_config=repository_config_mock)

        self.assertEqual(f"{self.obj_name} not found", exception_context.exception.detail)
        self.assertEqual(fastapi.status.HTTP_404_NOT_FOUND, exception_context.exception.status_code)

    def test__not_found_convert_flow(self):
        expected_result = MagicMock()
        result_mock = MagicMock()
        repository_config_mock = MagicMock()
        _raise_not_found_mock = self.patch_obj(target=self.repository_class, attribute="_raise_not_found")
        convert_one_result_mock = self.patch_obj(
            target=self.repository_class, attribute="convert_one_result", return_value=expected_result
        )

        result = self.repository_class._not_found_convert_flow(
            result=result_mock, repository_config=repository_config_mock
        )

        _raise_not_found_mock.assert_called_once_with(result=result_mock, repository_config=repository_config_mock)
        convert_one_result_mock.assert_called_once_with(result=result_mock, repository_config=repository_config_mock)
        self.assertEqual(expected_result, result)

    async def test_insert_one(self):
        document = {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()}

        # insert a new document to test database
        insert_one_result = await self.repository_class.insert_one(document=document)

        self.assertIsInstance(insert_one_result, InsertOneResult)
        self.assertIsInstance(insert_one_result.inserted_id, ObjectId)
        self.assertTrue(insert_one_result.acknowledged)

        # retrieve inserted document from test database
        inserted_document = await self.repository_class.find_one(query={"_id": document["_id"]})

        self.assertEqual(document, inserted_document)

    async def test_insert_many(self):
        documents = [
            {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()},
            {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()},
        ]

        insert_many_result = await self.repository_class.insert_many(documents=documents)

        self.assertIsInstance(insert_many_result, InsertManyResult)
        self.assertEqual([document["_id"] for document in documents], insert_many_result.inserted_ids)
        self.assertTrue(insert_many_result.acknowledged)

        inserted_documents = await self.repository_class.find(query={})

        self.assertEqual(documents, inserted_documents)

    async def test_replace_one(self):
        old_data_key, new_data_key = self.faker.pystr(), self.faker.pystr()
        old_document = {"_id": ObjectId(), old_data_key: self.faker.pystr()}
        await self.repository_class.insert_one(document=old_document)

        new_document = {new_data_key: self.faker.pystr()}

        replace_one_result = await self.repository_class.replace_one(
            query={"_id": old_document["_id"]}, replacement=new_document
        )

        self.assertIsInstance(replace_one_result, UpdateResult)
        self.assertEqual(1, replace_one_result.matched_count)
        self.assertEqual(1, replace_one_result.modified_count)
        self.assertIsNone(replace_one_result.upserted_id)
        self.assertTrue(replace_one_result.acknowledged)

        updated_old_document = await self.repository_class.find_one(query={"_id": old_document["_id"]})

        self.assertEqual(old_document["_id"], updated_old_document["_id"])  # check _id field not changed
        self.assertEqual(new_document[new_data_key], updated_old_document[new_data_key])

    async def test_update_one(self):
        old_data_key, new_data_value = self.faker.pystr(), self.faker.pystr()

        old_document = {"_id": ObjectId(), old_data_key: self.faker.pystr()}
        await self.repository_class.insert_one(document=old_document)

        update_one_result = await self.repository_class.update_one(
            query={"_id": old_document["_id"]}, update={"$set": {old_data_key: new_data_value}}
        )

        self.assertIsInstance(update_one_result, UpdateResult)
        self.assertEqual(1, update_one_result.matched_count)
        self.assertEqual(1, update_one_result.modified_count)
        self.assertIsNone(update_one_result.upserted_id)
        self.assertTrue(update_one_result.acknowledged)

        updated_old_document = await self.repository_class.find_one(query={"_id": old_document["_id"]})

        self.assertEqual(old_document["_id"], updated_old_document["_id"])
        self.assertEqual(new_data_value, updated_old_document[old_data_key])

    async def test_update_many(self):
        old_key, old_value, new_value = self.faker.pystr(), self.faker.pystr(), self.faker.pystr()
        documents = [
            {"_id": ObjectId(), old_key: old_value},
            {"_id": ObjectId(), old_key: old_value},
        ]
        expected_documents = [
            {"_id": documents[0]["_id"], old_key: new_value},
            {"_id": documents[1]["_id"], old_key: new_value},
        ]
        await self.repository_class.insert_many(documents=documents)

        update_many_result = await self.repository_class.update_many(query={}, update={"$set": {old_key: new_value}})

        self.assertIsInstance(update_many_result, UpdateResult)
        self.assertEqual(2, update_many_result.matched_count)
        self.assertEqual(2, update_many_result.modified_count)
        self.assertIsNone(update_many_result.upserted_id)
        self.assertTrue(update_many_result.acknowledged)

        find_result = await self.repository_class.find(query={})

        self.assertEqual(expected_documents, find_result)

    async def test_delete_one(self):
        document = {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()}
        await self.repository_class.insert_one(document=document)

        result = await self.repository_class.delete_one(query={"_id": document["_id"]})

        self.assertIsInstance(result, DeleteResult)
        self.assertEqual(1, result.deleted_count)
        self.assertTrue(result.acknowledged)

    async def test_delete_many(self):
        documents = [
            {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()},
            {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()},
        ]
        await self.repository_class.insert_many(documents=documents)

        result = await self.repository_class.delete_many(query={})

        self.assertIsInstance(result, DeleteResult)
        self.assertEqual(2, result.deleted_count)
        self.assertTrue(result.acknowledged)

    async def test_find(self):
        documents = [
            {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()},
            {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()},
        ]
        await self.repository_class.insert_many(documents=documents)

        result = await self.repository_class.find(query={})

        self.assertEqual(documents, result)

    async def test_find_one(self):
        document = {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()}
        await self.repository_class.insert_one(document=document)

        result = await self.repository_class.find_one(query={})

        self.assertEqual(document, result)

    async def test_find_one_and_delete(self):
        document = {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()}
        await self.repository_class.insert_one(document=document)

        result = await self.repository_class.find_one_and_delete(query={})

        self.assertEqual(document, result)

    async def test_find_one_and_replace(self):
        new_key = self.faker.pystr()
        document = {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()}
        replacement = {new_key: self.faker.pystr()}
        replaced_document = {"_id": document["_id"], new_key: replacement[new_key]}
        await self.repository_class.insert_one(document=document)

        result = await self.repository_class.find_one_and_replace(query={}, replacement=replacement)

        self.assertEqual(document, result)

        replaced_document_result = await self.repository_class.find_one(query={})

        self.assertEqual(replaced_document, replaced_document_result)

    async def test_find_one_and_update(self):
        old_data_key, new_data_value = self.faker.pystr(), self.faker.pystr()

        old_document = {"_id": ObjectId(), old_data_key: self.faker.pystr()}
        updated_document = {"_id": old_document["_id"], old_data_key: new_data_value}
        await self.repository_class.insert_one(document=old_document)

        find_one_and_update_result = await self.repository_class.find_one_and_update(
            query={"_id": old_document["_id"]}, update={"$set": {old_data_key: new_data_value}}
        )

        self.assertEqual(old_document, find_one_and_update_result)

        updated_document_result = await self.repository_class.find_one(query={})

        self.assertEqual(updated_document, updated_document_result)

    async def test_count_documents(self):
        counter = self.faker.pyint(min_value=2, max_value=10)
        documents = []
        for _ in range(counter):
            documents.append({"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()})
        await self.repository_class.insert_many(documents=documents)

        result = await self.repository_class.count_documents(query={})

        self.assertEqual(counter, result)

    async def test_estimated_document_count(self):
        counter = self.faker.pyint(min_value=2, max_value=10)
        documents = []
        for _ in range(counter):
            documents.append({"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()})
        await self.repository_class.insert_many(documents=documents)

        result = await self.repository_class.estimated_document_count(query={})

        self.assertEqual(counter, result)

    async def test_aggregate(self):
        documents = [
            {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()},
            {"_id": ObjectId(), self.faker.pystr(): self.faker.pystr()},
        ]
        await self.repository_class.insert_many(documents=documents)

        result = await self.repository_class.aggregate(pipeline=[])

        self.assertEqual(documents, result)

    async def test_bulk_write(self):
        _id, field_name, expected_count = ObjectId(), self.faker.pystr(), 1
        _check_attrs_list = ["deleted_count", "inserted_count", "matched_count", "modified_count", "upserted_count"]
        operations = [
            pymongo.operations.UpdateOne(
                filter={"_id": _id}, update={"$set": {field_name: self.faker.pystr()}}, upsert=True
            ),
            pymongo.operations.InsertOne(document={"_id": ObjectId(), field_name: self.faker.pystr()}),
            pymongo.operations.UpdateOne(filter={"_id": _id}, update={"$set": {field_name: self.faker.pystr()}}),
            pymongo.operations.DeleteOne(filter={"_id": _id}),
        ]

        result = await self.repository_class.bulk_write(operations=operations)

        self.assertIsInstance(result, pymongo.results.BulkWriteResult)
        self.assertTrue(result.acknowledged)
        self.assertIn(_id, result.upserted_ids.values())
        for attr in _check_attrs_list:
            self.assertEqual(expected_count, getattr(result, attr))
