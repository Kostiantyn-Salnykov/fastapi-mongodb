import typing
from unittest.mock import MagicMock, call

import motor.motor_asyncio
import pymongo
import pymongo.errors

import bases
import settings


class TestCommandLogger(bases.helpers.AsyncTestCaseWithPathing):
    def setUp(self) -> None:
        self.logger = bases.db.CommandLogger()
        self.event = MagicMock()
        self.debug_mock = self.patch_obj(target=bases.logging.logger, attribute="debug")

    def test_started(self):
        self.logger.started(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"Command '{self.event.command_name}' with request id {self.event.request_id} started on server "
            f"{self.event.connection_id}"
        )

    def test_succeeded(self):
        self.logger.succeeded(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"Command '{self.event.command_name}' with request id {self.event.request_id} on server "
            f"{self.event.connection_id} succeeded in {self.event.duration_micros} microseconds"
        )

    def test_failed(self):
        self.logger.failed(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"Command {self.event.command_name} with request id {self.event.request_id} on server "
            f"{self.event.connection_id} failed in {self.event.duration_micros} microseconds"
        )


class TestConnectionPoolLogger(bases.helpers.AsyncTestCaseWithPathing):
    def setUp(self) -> None:
        self.logger = bases.db.ConnectionPoolLogger()
        self.event = MagicMock()
        self.debug_mock = self.patch_obj(target=bases.logging.logger, attribute="debug")

    def test_pool_created(self):
        self.logger.pool_created(event=self.event)

        self.debug_mock.assert_called_once_with(f"[pool {self.event.address}] pool created")

    def test_pool_cleared(self):
        self.logger.pool_cleared(event=self.event)

        self.debug_mock.assert_called_once_with(f"[pool {self.event.address}] pool cleared")

    def test_pool_closed(self):
        self.logger.pool_closed(event=self.event)

        self.debug_mock.assert_called_once_with(f"[pool {self.event.address}] pool closed")

    def test_connection_created(self):
        self.logger.connection_created(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"[pool {self.event.address}][conn #{self.event.connection_id}] connection created"
        )

    def test_connection_ready(self):
        self.logger.connection_ready(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"[pool {self.event.address}][conn #{self.event.connection_id}] connection setup succeeded"
        )

    def test_connection_closed(self):
        self.logger.connection_closed(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"[pool {self.event.address}][conn #{self.event.connection_id}] connection closed, reason: "
            f"{self.event.reason}"
        )

    def test_connection_check_out_started(self):
        self.logger.connection_check_out_started(event=self.event)

        self.debug_mock.assert_called_once_with(f"[pool {self.event.address}] connection check out started")

    def test_connection_check_out_failed(self):
        self.logger.connection_check_out_failed(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"[pool {self.event.address}] connection check out failed, reason: {self.event.reason}"
        )

    def test_connection_checked_out(self):
        self.logger.connection_checked_out(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"[pool {self.event.address}][conn #{self.event.connection_id}] connection checked out of pool"
        )

    def test_connection_checked_in(self):
        self.logger.connection_checked_in(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"[pool {self.event.address}][conn #{self.event.connection_id}] connection checked into pool"
        )


class TestServerLogger(bases.helpers.AsyncTestCaseWithPathing):
    def setUp(self) -> None:
        self.logger = bases.db.ServerLogger()
        self.event = MagicMock()
        self.debug_mock = self.patch_obj(target=bases.logging.logger, attribute="debug")

    def test_opened(self):
        self.logger.opened(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"Server {self.event.server_address} added to topology {self.event.topology_id}"
        )

    def test_description_changed(self):
        self.logger.description_changed(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"Server {self.event.server_address} changed type from {self.event.previous_description.server_type_name} "
            f"to {self.event.new_description.server_type_name}"
        )

    def test_closed(self):
        self.logger.closed(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"Server {self.event.server_address} removed from topology {self.event.topology_id}"
        )


class TestHeartbeatLogger(bases.helpers.AsyncTestCaseWithPathing):
    def setUp(self) -> None:
        self.logger = bases.db.HeartbeatLogger()
        self.event = MagicMock()
        self.debug_mock = self.patch_obj(target=bases.logging.logger, attribute="debug")

    def test_started(self):
        self.logger.started(event=self.event)

        self.debug_mock.assert_called_once_with(f"Heartbeat sent to server {self.event.connection_id}")

    def test_succeeded(self):
        self.logger.succeeded(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"Heartbeat to server {self.event.connection_id} succeeded with reply {self.event.reply.document}"
        )

    def test_failed(self):
        self.logger.failed(event=self.event)

        self.debug_mock.assert_called_once_with(
            f"Heartbeat to server {self.event.connection_id} failed with error {self.event.reply}"
        )


class TestTopologyLogger(bases.helpers.AsyncTestCaseWithPathing):
    def setUp(self) -> None:
        self.logger = bases.db.TopologyLogger()
        self.event = MagicMock()
        self.debug_mock = self.patch_obj(target=bases.logging.logger, attribute="debug")

    def test_opened(self):
        self.logger.opened(event=self.event)

        self.debug_mock.assert_called_once_with(f"Topology with id {self.event.topology_id} opened")

    def test_description_changed(self):
        self.event.new_description.has_writable_server.return_value = False
        self.event.new_description.has_readable_server.return_value = False

        self.logger.description_changed(event=self.event)

        self.debug_mock.assert_has_calls(
            calls=[
                call(f"Topology description updated for topology id {self.event.topology_id}"),
                call(
                    f"Topology {self.event.topology_id} changed type from "
                    f"{self.event.previous_description.topology_type_name} to "
                    f"{self.event.new_description.topology_type_name}"
                ),
                call("No writable servers available."),
                call("No readable servers available."),
            ]
        )

    def test_closed(self):
        self.logger.closed(event=self.event)

        self.debug_mock.assert_called_once_with(f"Topology with id {self.event.topology_id} closed")


class TestMongoDBHandler(bases.helpers.MongoDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_db_name = settings.Settings.MONGO_TEST_DB_NAME
        self.mongo_handler = bases.db.MongoDBHandler()
        self.debug_mock = self.patch_obj(target=bases.logging.logger, attribute="debug")

    def test_retrieve_client(self):
        result = self.mongo_handler.retrieve_client()

        self.assertEqual(self._get_client_for_test(), result)

    def test_create_client(self):
        self.assertIsNone(self.mongo_handler.client)

        self.mongo_handler.create_client()

        self.assertIsInstance(self.mongo_handler.client, motor.motor_asyncio.AsyncIOMotorClient)

    def test_delete_client(self):
        self.assertIsInstance(self.mongo_handler.client, motor.motor_asyncio.AsyncIOMotorClient)

        self.mongo_handler.delete_client()

        self.assertIsNone(self.mongo_handler.client)

    async def test_get_server_info(self):
        result = await self.mongo_handler.get_server_info()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["ok"], 1.0)

    def test_retrieve_database(self):
        result = self.mongo_handler.retrieve_database()

        self.assertIsInstance(result, motor.motor_asyncio.AsyncIOMotorDatabase)
        self.assertEqual(result.name, settings.Settings.MONGO_TEST_DB_NAME)

    async def test_list_databases(self):
        _required_dbs = ["admin", "config", "local"]  # MongoDB predefined DBs

        result: list[dict[str, typing.Any]] = await self.mongo_handler.list_databases()

        self.assertTrue(all(required_db in [db["name"] for db in result] for required_db in _required_dbs))

        result2: list[str] = await self.mongo_handler.list_databases(only_names=True)

        self.assertTrue(all(required_db in result2 for required_db in _required_dbs))

    async def test_delete_database(self):
        await self.mongo_handler.create_collection(name=self.faker.pystr(), db_name=self.faker.pystr())
        db_names = await self.mongo_handler.list_databases(only_names=True)
        self.assertIn(self.test_db_name, db_names)

        await self.mongo_handler.delete_database(name=self.test_db_name)

        updated_db_names = await self.mongo_handler.list_databases(only_names=True)

        self.assertNotIn(self.test_db_name, updated_db_names)

    async def test_set_get_profiling_level(self):
        default_level = pymongo.OFF  # default level is 0
        new_level = pymongo.SLOW_ONLY
        self.assertEqual(default_level, await self.mongo_handler.get_profiling_level(db_name=self.test_db_name))

        await self.mongo_handler.set_profiling_level(db_name=self.test_db_name, level=new_level, slow_ms=10)

        self.assertEqual(new_level, await self.mongo_handler.get_profiling_level(db_name=self.test_db_name))

    async def test_get_profiling_info(self):
        col_name = self.faker.pystr()
        level, op, ns = pymongo.ALL, "command", f"{self.test_db_name}.{col_name}"
        await self.mongo_handler.set_profiling_level(db_name=self.test_db_name, level=level)
        await self.mongo_handler.create_collection(name=col_name, db_name=self.test_db_name)

        result = await self.mongo_handler.get_profiling_info(db_name=self.test_db_name)

        self.assertIsInstance(result, list)
        self.assertEqual(op, result[0]["op"])
        self.assertEqual(ns, result[0]["ns"])

    async def test_create_collection(self):
        col_name = self.faker.pystr()
        col_names = await self.mongo_handler.list_collections(db_name=self.test_db_name, only_names=True)
        self.assertNotIn(col_name, col_names)

        collection = await self.mongo_handler.create_collection(name=col_name, db_name=self.test_db_name)

        updated_col_names = await self.mongo_handler.list_collections(db_name=self.test_db_name, only_names=True)
        self.assertIn(col_name, updated_col_names)
        self.assertIsInstance(collection, motor.motor_asyncio.AsyncIOMotorCollection)
        self.assertEqual(col_name, collection.name)
        self.assertEqual(self.test_db_name, collection.database.name)

    async def test_create_collection_not_safe(self):
        col_name = self.faker.pystr()
        await self.mongo_handler.create_collection(name=col_name, db_name=self.test_db_name)

        with self.assertRaises(pymongo.errors.CollectionInvalid) as exception_context:
            await self.mongo_handler.create_collection(name=col_name, db_name=self.test_db_name, safe=False)

        self.assertEqual(f"collection {col_name} already exists", str(exception_context.exception))

    async def test_delete_collection(self):
        col_name = self.faker.pystr()
        await self.mongo_handler.create_collection(name=col_name, db_name=self.test_db_name)
        col_names = await self.mongo_handler.list_collections(db_name=self.test_db_name, only_names=True)
        self.assertIn(col_name, col_names)

        await self.mongo_handler.delete_collection(name=col_name, db_name=self.test_db_name)

        updated_col_names = await self.mongo_handler.list_collections(db_name=self.test_db_name, only_names=True)
        self.assertNotIn(col_name, updated_col_names)

    async def test_list_collections(self):
        col_name, col_type = self.faker.pystr(), "collection"
        await self.mongo_handler.create_collection(name=col_name, db_name=self.test_db_name)

        result: list[dict[str, typing.Any]] = await self.mongo_handler.list_collections(db_name=self.test_db_name)

        self.assertEqual(col_name, result[0]["name"])
        self.assertEqual(col_type, result[0]["type"])

    async def test_list_collections_only_names(self):
        col_name = self.faker.pystr()
        await self.mongo_handler.create_collection(name=col_name, db_name=self.test_db_name)

        result = await self.mongo_handler.list_collections(db_name=self.test_db_name, only_names=True)

        self.assertIn(col_name, result)

    async def test_create_index(self):
        index_name, col_name = self.faker.pystr(), self.faker.pystr()
        indexes_names = await self.mongo_handler.list_indexes(
            col_name=col_name, db_name=self.test_db_name, only_names=True
        )
        self.assertNotIn(index_name, indexes_names)

        result = await self.mongo_handler.create_index(
            col_name=col_name, db_name=self.test_db_name, name=index_name, index=[("test", pymongo.ASCENDING)]
        )

        updated_indexes_names = await self.mongo_handler.list_indexes(
            col_name=col_name, db_name=self.test_db_name, only_names=True
        )
        self.assertIn(index_name, updated_indexes_names)
        self.assertEqual(index_name, result)

    async def test_create_indexes(self):
        index_name, index_name2, col_name = self.faker.pystr(), self.faker.pystr(), self.faker.pystr()
        indexes = [
            pymongo.IndexModel(name=index_name, keys=[("test", pymongo.ASCENDING)]),
            pymongo.IndexModel(name=index_name2, keys=[("test2", pymongo.DESCENDING)]),
        ]

        result = await self.mongo_handler.create_indexes(col_name=col_name, db_name=self.test_db_name, indexes=indexes)

        self.assertEqual([index_name, index_name2], result)

    async def test_delete_index(self):
        index_name, col_name = self.faker.pystr(), self.faker.pystr()
        await self.mongo_handler.create_index(
            col_name=col_name, db_name=self.test_db_name, name=index_name, index=[("test", pymongo.ASCENDING)]
        )
        indexes_names = await self.mongo_handler.list_indexes(
            col_name=col_name, db_name=self.test_db_name, only_names=True
        )
        self.assertIn(index_name, indexes_names)

        await self.mongo_handler.delete_index(col_name=col_name, db_name=self.test_db_name, name=index_name)

        updated_indexes_names = await self.mongo_handler.list_indexes(
            col_name=col_name, db_name=self.test_db_name, only_names=True
        )
        self.assertNotIn(index_name, updated_indexes_names)

    async def test_delete_index_not_safe(self):
        index_name, col_name = self.faker.pystr(), self.faker.pystr()
        expected_exception_details = {
            "ok": 0.0,
            "errmsg": f"index not found with name [{index_name}]",
            "code": 27,
            "codeName": "IndexNotFound"
        }
        await self.mongo_handler.create_collection(name=col_name, db_name=self.test_db_name)

        with self.assertRaises(pymongo.errors.OperationFailure) as exception_context:
            await self.mongo_handler.delete_index(
                col_name=col_name, db_name=self.test_db_name, name=index_name, safe=False
            )

        self.assertDictEqual(expected_exception_details, exception_context.exception.details)

    async def test_list_indexes_names(self):
        index_name, col_name = self.faker.pystr(), self.faker.pystr()
        await self.mongo_handler.create_index(
            col_name=col_name, db_name=self.test_db_name, name=index_name, index=[("test", pymongo.ASCENDING)]
        )

        result = await self.mongo_handler.list_indexes(col_name=col_name, db_name=self.test_db_name, only_names=True)

        self.assertIn(index_name, result)

    async def test_list_indexes(self):
        index_name, col_name = self.faker.pystr(), self.faker.pystr()
        index_key, index_order = "test", pymongo.ASCENDING
        index_keys = [(index_key, index_order)]
        await self.mongo_handler.create_index(
            col_name=col_name, db_name=self.test_db_name, name=index_name, index=index_keys
        )

        result = await self.mongo_handler.list_indexes(col_name=col_name, db_name=self.test_db_name)

        created_index_son = result[-1]
        self.assertEqual(index_name, created_index_son["name"])
        self.assertEqual(index_order, created_index_son["key"][index_key])
        self.assertTrue(created_index_son["background"])
        self.assertFalse(created_index_son["sparse"])
