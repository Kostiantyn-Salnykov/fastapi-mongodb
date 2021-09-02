import datetime
import decimal
import random
import typing
import unittest.mock

import bson
import motor.motor_asyncio
import pymongo.errors
import pytest

import fastapi_mongodb.db
import fastapi_mongodb.helpers
import fastapi_mongodb.logging

pytestmark = [pytest.mark.asyncio]


class TestBaseDocument:
    def setup_method(self) -> None:
        self.base_document = fastapi_mongodb.db.BaseDocument()

    def test__eq__(self, faker):
        data_1, data_2 = faker.pydict(), faker.pydict()
        fake_type = random.choice(
            [faker.pystr, faker.pybool, faker.pyfloat, faker.pyint, faker.pylist, faker.pyset, faker.pydecimal]
        )()
        document_1 = fastapi_mongodb.db.BaseDocument(data=data_1)
        document_2 = fastapi_mongodb.db.BaseDocument(data=data_2)

        assert data_1 == document_1
        assert data_2 == document_2
        assert data_1 != document_2
        assert data_2 != document_1
        assert document_1 != document_2
        assert fake_type != document_1

    def test_properties(self):
        assert self.base_document.oid is None
        assert self.base_document.id is None
        assert self.base_document.data == {}
        oid = bson.ObjectId()

        self.base_document["_id"] = oid

        assert self.base_document.oid == oid
        assert self.base_document.id == str(oid)
        assert self.base_document.data == {"_id": oid}
        assert self.base_document.generated_at == oid.generation_time.astimezone(
            tz=fastapi_mongodb.helpers.get_utc_timezone()
        )

    def test_getitem_setitem_delitem(self, faker):
        # test getitem
        with pytest.raises(KeyError) as exception_context:
            _ = self.base_document["test"]
        assert str(exception_context.value) == str(KeyError("test"))
        assert self.base_document.get("test", None) is None
        fake_test = faker.pystr()

        # test setitem
        self.base_document["test"] = fake_test
        assert self.base_document["test"] == fake_test

        # test delitem
        del self.base_document["test"]
        assert self.base_document.get("test", None) is None


class TestDecimalCode:
    def setup_method(self) -> None:
        self.codec = fastapi_mongodb.db.DecimalCodec()

    def test_transform(self, faker):
        value = faker.pydecimal()

        bson_value = self.codec.transform_python(value=value)
        python_value = self.codec.transform_bson(value=bson_value)

        assert isinstance(bson_value, bson.Decimal128)
        assert isinstance(python_value, decimal.Decimal)
        assert value == python_value


class TestTimeDeltaCodec:
    def setup_method(self) -> None:
        self.codec = fastapi_mongodb.db.TimeDeltaCodec()

    def test_transform(self, faker):
        value = faker.time_delta(end_datetime=faker.future_datetime())

        bson_value = self.codec.transform_python(value=value)
        python_value = self.codec.transform_bson(value=bson_value)

        assert isinstance(bson_value, str)
        assert isinstance(python_value, datetime.timedelta)
        assert value == python_value

    def test_transform_0_micros(self):
        weeks, days, hours, minutes, seconds = 1, 2, 3, 4, 5
        bson_value = f"P{weeks}W{days}DT{hours}H{minutes}M{seconds}S"
        expected_time_delta = datetime.timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)

        python_value = self.codec.transform_bson(value=bson_value)

        assert expected_time_delta == python_value


@pytest.fixture()
def patch_logging(patcher):
    yield patcher.patch_attr(target=fastapi_mongodb.logging.simple_logger, attribute="debug")


@pytest.fixture()
def event():
    return unittest.mock.MagicMock()


class TestCommandLogger:
    @classmethod
    def setup_class(cls) -> None:
        cls.logger = fastapi_mongodb.db.CommandLogger()

    def test_started(self, patch_logging, event):
        self.logger.started(event=event)

        patch_logging.assert_called_once_with(
            f"Command '{event.command_name}' with request id {event.request_id} started on server "
            f"{event.connection_id}"
        )

    def test_succeeded(self, patch_logging, event):
        self.logger.succeeded(event=event)

        patch_logging.assert_called_once_with(
            f"Command '{event.command_name}' with request id {event.request_id} on server "
            f"{event.connection_id} succeeded in {event.duration_micros} microseconds"
        )

    def test_failed(self, patch_logging, event):
        self.logger.failed(event=event)

        patch_logging.assert_called_once_with(
            f"Command {event.command_name} with request id {event.request_id} on server "
            f"{event.connection_id} failed in {event.duration_micros} microseconds"
        )


class TestConnectionPoolLogger:
    @classmethod
    def setup_class(cls) -> None:
        cls.logger = fastapi_mongodb.db.ConnectionPoolLogger()

    def test_pool_created(self, patch_logging, event):
        self.logger.pool_created(event=event)

        patch_logging.assert_called_once_with(f"[pool {event.address}] pool created")

    def test_pool_cleared(self, patch_logging, event):
        self.logger.pool_cleared(event=event)

        patch_logging.assert_called_once_with(f"[pool {event.address}] pool cleared")

    def test_pool_closed(self, patch_logging, event):
        self.logger.pool_closed(event=event)

        patch_logging.assert_called_once_with(f"[pool {event.address}] pool closed")

    def test_connection_created(self, patch_logging, event):
        self.logger.connection_created(event=event)

        patch_logging.assert_called_once_with(f"[pool {event.address}][conn #{event.connection_id}] connection created")

    def test_connection_ready(self, patch_logging, event):
        self.logger.connection_ready(event=event)

        patch_logging.assert_called_once_with(
            f"[pool {event.address}][conn #{event.connection_id}] connection setup succeeded"
        )

    def test_connection_closed(self, patch_logging, event):
        self.logger.connection_closed(event=event)

        patch_logging.assert_called_once_with(
            f"[pool {event.address}][conn #{event.connection_id}] connection closed, reason: {event.reason}"
        )

    def test_connection_check_out_started(self, patch_logging, event):
        self.logger.connection_check_out_started(event=event)

        patch_logging.assert_called_once_with(f"[pool {event.address}] connection check out started")

    def test_connection_check_out_failed(self, patch_logging, event):
        self.logger.connection_check_out_failed(event=event)

        patch_logging.assert_called_once_with(
            f"[pool {event.address}] connection check out failed, reason: {event.reason}"
        )

    def test_connection_checked_out(self, patch_logging, event):
        self.logger.connection_checked_out(event=event)

        patch_logging.assert_called_once_with(
            f"[pool {event.address}][conn #{event.connection_id}] connection checked out of pool"
        )

    def test_connection_checked_in(self, patch_logging, event):
        self.logger.connection_checked_in(event=event)

        patch_logging.assert_called_once_with(
            f"[pool {event.address}][conn #{event.connection_id}] connection checked into pool"
        )


class TestServerLogger:
    @classmethod
    def setup_class(cls) -> None:
        cls.logger = fastapi_mongodb.db.ServerLogger()

    def test_opened(self, patch_logging, event):
        self.logger.opened(event=event)

        patch_logging.assert_called_once_with(f"Server {event.server_address} added to topology {event.topology_id}")

    def test_description_changed_called(self, patch_logging, event):
        new_mock = unittest.mock.MagicMock()
        event.new_description.server_type = new_mock
        self.logger.description_changed(event=event)

        patch_logging.assert_called_once_with(
            f"Server {event.server_address} changed type from {event.previous_description.server_type_name} to "
            f"{event.new_description.server_type_name}"
        )

    def test_description_changed_not_called(self, patch_logging, event):
        new_mock = unittest.mock.MagicMock()
        event.previous_description.server_type = new_mock
        event.new_description.server_type = new_mock
        self.logger.description_changed(event=event)

        patch_logging.assert_not_called()

    def test_closed(self, patch_logging, event):
        self.logger.closed(event=event)

        patch_logging.assert_called_once_with(
            f"Server {event.server_address} removed from topology {event.topology_id}"
        )


class TestHeartbeatLogger:
    @classmethod
    def setup_class(cls) -> None:
        cls.logger = fastapi_mongodb.db.HeartbeatLogger()

    def test_started(self, patch_logging, event):
        self.logger.started(event=event)

        patch_logging.assert_called_once_with(f"Heartbeat sent to server {event.connection_id}")

    def test_succeeded(self, patch_logging, event):
        self.logger.succeeded(event=event)

        patch_logging.assert_called_once_with(
            f"Heartbeat to server {event.connection_id} succeeded with reply {event.reply.document}"
        )

    def test_failed(self, patch_logging, event):
        self.logger.failed(event=event)

        patch_logging.assert_called_once_with(
            f"Heartbeat to server {event.connection_id} failed with error {event.reply}"
        )


class TestTopologyLogger:
    @classmethod
    def setup_class(cls) -> None:
        cls.logger = fastapi_mongodb.db.TopologyLogger()

    def test_opened(self, patch_logging, event):
        self.logger.opened(event=event)

        patch_logging.assert_called_once_with(f"Topology with id {event.topology_id} opened")

    def test_description_changed(self, patch_logging, event):
        event.new_description.has_writable_server.return_value = False
        event.new_description.has_readable_server.return_value = False
        self.logger.description_changed(event=event)

        patch_logging.assert_has_calls(
            calls=[
                unittest.mock.call(f"Topology description updated for topology id {event.topology_id}"),
                unittest.mock.call(
                    f"Topology {event.topology_id} changed type from {event.previous_description.topology_type_name} "
                    f"to {event.new_description.topology_type_name}"
                ),
                unittest.mock.call("No writable servers available."),
                unittest.mock.call("No readable servers available."),
            ]
        )

    def test_description_changed_not_changed(self, patch_logging, event):
        mock_topology_type = unittest.mock.MagicMock()
        event.previous_description.topology_type = mock_topology_type
        event.new_description.topology_type = mock_topology_type
        self.logger.description_changed(event=event)

        patch_logging.assert_called_once_with(f"Topology description updated for topology id {event.topology_id}")

    def test_closed(self, patch_logging, event):
        self.logger.closed(event=event)

        patch_logging.assert_called_once_with(f"Topology with id {event.topology_id} closed")


class TestDBHandler:
    @classmethod
    def setup_class(cls) -> None:
        cls.test_db = "test_db"

    @pytest.fixture()
    async def setup_indexes(self, db_manager, faker, mongodb_session):
        index_name, col_name = faker.pystr(), faker.pystr()
        await db_manager.create_index(
            col_name=col_name,
            db_name=self.test_db,
            name=index_name,
            index=[("test", pymongo.ASCENDING)],
            session=mongodb_session,
        )
        indexes_names = await db_manager.list_indexes(
            col_name=col_name, db_name=self.test_db, only_names=True, session=mongodb_session
        )
        assert index_name in indexes_names
        return index_name, col_name

    def test_create_client(self, db_manager):
        result = db_manager.create_client()

        assert result is None

    def test_delete_client(self, db_manager):
        result = db_manager.delete_client()

        assert result is None

    def test_retrieve_client(self, db_manager):
        result = db_manager.retrieve_client()

        assert result.__class__ == motor.motor_asyncio.AsyncIOMotorClient

    def test_retrieve_database(self, db_manager):
        result = db_manager.retrieve_database()

        assert result.__class__ == motor.motor_asyncio.AsyncIOMotorDatabase
        assert result.name == "test_db"

    async def test_get_server_info(self, db_manager, mongodb_session):
        result = await db_manager.get_server_info(session=mongodb_session)

        assert dict == result.__class__
        assert 1.0 == result["ok"]

    async def test_list_databases(self, db_manager, mongodb_session):
        required_dbs = ["admin", "local"]

        result: list[dict[str, typing.Any()]] = await db_manager.list_databases(session=mongodb_session)
        result_2: list[str] = await db_manager.list_databases(only_names=True, session=mongodb_session)

        assert all(required_db in [db["name"] for db in result] for required_db in required_dbs)
        assert all(required_db in result_2 for required_db in required_dbs)

    async def test_delete_database(self, db_manager, faker, mongodb_session):
        test_db = self.test_db
        await db_manager.create_collection(name=faker.pystr(), db_name=faker.pystr())
        db_names = await db_manager.list_databases(only_names=True, session=mongodb_session)
        assert test_db in db_names

        await db_manager.delete_database(name=test_db, session=mongodb_session)

        updated_db_names = await db_manager.list_databases(only_names=True, session=mongodb_session)

        assert test_db not in updated_db_names

    async def test_set_get_profiling_level(self, db_manager, mongodb_session):
        default_level = 0  # OFF
        new_level = 2  # ALL
        assert default_level == await db_manager.get_profiling_level(db_name=self.test_db, session=mongodb_session)

        result = await db_manager.set_profiling_level(
            db_name=self.test_db, level=new_level, slow_ms=0, session=mongodb_session
        )

        assert default_level == result["was"]
        assert 1.0 == result["ok"]
        assert new_level == await db_manager.get_profiling_level(db_name=self.test_db, session=mongodb_session)

    async def test_get_profiling_info(self, db_manager, faker, mongodb_session):
        col_name = faker.pystr()
        level = 2
        await db_manager.set_profiling_level(db_name=self.test_db, level=level, session=mongodb_session)
        await db_manager.create_collection(name=col_name, db_name=self.test_db, session=mongodb_session)
        result = await db_manager.get_profiling_info(db_name=self.test_db, session=mongodb_session)

        assert list == result.__class__
        assert "command" == result[0]["op"]

    async def test_create_collection(self, db_manager, faker, mongodb_session):
        col_name = faker.pystr()
        col_names = await db_manager.list_collections(db_name=self.test_db, only_names=True, session=mongodb_session)
        assert col_name not in col_names

        collection = await db_manager.create_collection(name=col_name, db_name=self.test_db, session=mongodb_session)

        updated_col_names = await db_manager.list_collections(
            db_name=self.test_db, only_names=True, session=mongodb_session
        )
        assert col_name in updated_col_names
        assert motor.motor_asyncio.AsyncIOMotorCollection == collection.__class__
        assert col_name == collection.name
        assert self.test_db == collection.database.name

    async def test_create_collection_not_safe(self, db_manager, faker, mongodb_session):
        col_name = faker.pystr()
        await db_manager.create_collection(name=col_name, db_name=self.test_db, session=mongodb_session)

        with pytest.raises(pymongo.errors.CollectionInvalid) as exception_context:
            await db_manager.create_collection(name=col_name, db_name=self.test_db, safe=False, session=mongodb_session)
        await db_manager.create_collection(name=col_name, db_name=self.test_db, session=mongodb_session)

        assert f"collection {col_name} already exists" == str(exception_context.value)

    async def test_delete_collection(self, db_manager, faker, mongodb_session):
        col_name = faker.pystr()
        await db_manager.create_collection(name=col_name, db_name=self.test_db, session=mongodb_session)
        col_names = await db_manager.list_collections(db_name=self.test_db, only_names=True, session=mongodb_session)
        assert col_name in col_names

        await db_manager.delete_collection(name=col_name, db_name=self.test_db, session=mongodb_session)

        updated_col_names = await db_manager.list_collections(
            db_name=self.test_db, only_names=True, session=mongodb_session
        )
        assert col_name not in updated_col_names

    async def test_list_collections(self, db_manager, faker, mongodb_session):
        col_name, col_type = faker.pystr(), "collection"
        await db_manager.create_collection(name=col_name, db_name=self.test_db, session=mongodb_session)

        result: list[dict[str, typing.Any]] = await db_manager.list_collections(
            db_name=self.test_db, session=mongodb_session
        )

        for i, col in enumerate(result):
            if col["name"] == col_name:
                assert col_type == result[i]["type"]

    async def test_list_collections_only_names(self, db_manager, faker, mongodb_session):
        col_name = faker.pystr()
        await db_manager.create_collection(name=col_name, db_name=self.test_db, session=mongodb_session)

        result = await db_manager.list_collections(db_name=self.test_db, only_names=True, session=mongodb_session)

        assert col_name in result

    async def test_create_index(self, db_manager, faker, mongodb_session):
        index_name, col_name = faker.pystr(), faker.pystr()
        indexes_names = await db_manager.list_indexes(
            col_name=col_name, db_name=self.test_db, only_names=True, session=mongodb_session
        )
        assert index_name not in indexes_names

        result = await db_manager.create_index(
            col_name=col_name,
            db_name=self.test_db,
            name=index_name,
            index=[("test", pymongo.ASCENDING)],
            session=mongodb_session,
        )

        updated_indexes_names = await db_manager.list_indexes(
            col_name=col_name, db_name=self.test_db, only_names=True, session=mongodb_session
        )
        assert index_name in updated_indexes_names
        assert index_name == result

    async def test_create_indexes(self, db_manager, faker, mongodb_session):
        index_name, index_name2, col_name = faker.pystr(), faker.pystr(), faker.pystr()
        indexes = [
            pymongo.IndexModel(name=index_name, keys=[("test", pymongo.ASCENDING)]),
            pymongo.IndexModel(name=index_name2, keys=[("test2", pymongo.DESCENDING)]),
        ]

        result = await db_manager.create_indexes(
            col_name=col_name, db_name=self.test_db, indexes=indexes, session=mongodb_session
        )

        assert [index_name, index_name2] == result

    async def test_delete_index(self, db_manager, setup_indexes, mongodb_session):
        index_name, col_name = setup_indexes
        await db_manager.delete_index(col_name=col_name, db_name=self.test_db, name=index_name, session=mongodb_session)

        updated_indexes_names = await db_manager.list_indexes(
            col_name=col_name, db_name=self.test_db, only_names=True, session=mongodb_session
        )
        assert index_name not in updated_indexes_names

    async def test_delete_index_not_safe(self, db_manager, faker, mongodb_session):
        index_name, col_name = faker.pystr(), faker.pystr()
        expected_exception_details = {
            "ok": 0.0,
            "errmsg": f"index not found with name [{index_name}]",
            "code": 27,
            "codeName": "IndexNotFound",
        }
        await db_manager.create_collection(name=col_name, db_name=self.test_db, session=mongodb_session)

        with pytest.raises(pymongo.errors.OperationFailure) as exception_context:
            await db_manager.delete_index(
                col_name=col_name, db_name=self.test_db, name=index_name, safe=False, session=mongodb_session
            )
        await db_manager.delete_index(col_name=col_name, db_name=self.test_db, name=index_name, session=mongodb_session)

        for key, value in expected_exception_details.items():
            assert value == exception_context.value.details[key]

    async def test_list_indexes_names(self, db_manager, faker, setup_indexes):
        """Same logic as in setup_indexes"""

    async def test_list_indexes(self, db_manager, faker, mongodb_session):
        index_name, col_name = faker.pystr(), faker.pystr()
        index_key, index_order = "test", pymongo.ASCENDING
        index_keys = [(index_key, index_order)]
        await db_manager.create_index(
            col_name=col_name, db_name=self.test_db, name=index_name, index=index_keys, session=mongodb_session
        )

        result = await db_manager.list_indexes(col_name=col_name, db_name=self.test_db, session=mongodb_session)

        created_index_son = result[-1]
        assert index_name == created_index_son["name"]
        assert index_order == created_index_son["key"][index_key]
        assert created_index_son["background"]
        assert not created_index_son["sparse"]
