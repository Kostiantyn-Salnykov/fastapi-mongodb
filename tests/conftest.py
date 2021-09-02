import asyncio
import unittest.mock

import motor.motor_asyncio
import pytest
from _pytest.monkeypatch import MonkeyPatch
from faker import Faker

import fastapi_mongodb.db

pytestmark = [pytest.mark.asyncio]


@pytest.fixture()
def faker() -> "Faker":
    return Faker()


class Patcher:
    def __init__(self):
        self.current_patcher = None

    def patch_obj(self, target: str, **kwargs):
        self.current_patcher = unittest.mock.patch(target=target, **kwargs)
        return self.current_patcher.start()

    def patch_attr(self, target, attribute: str, **kwargs):
        self.current_patcher = unittest.mock.patch.object(target=target, attribute=attribute, **kwargs)
        return self.current_patcher.start()

    def patch_property(self, target, attribute: str, return_value, **kwargs):
        self.current_patcher = unittest.mock.patch.object(
            target=target, attribute=attribute, new=unittest.mock.PropertyMock(return_value=return_value), **kwargs
        )
        return self.current_patcher.start()

    def stop(self):
        if self.current_patcher is not None:
            self.current_patcher.stop()


@pytest.fixture(scope="function")
def patcher() -> "Patcher":
    _patcher = Patcher()
    yield _patcher
    _patcher.current_patcher.stop()


@pytest.fixture(scope="session", autouse=True)
def monkeypatch_session() -> "MonkeyPatch":
    monkey_patch = MonkeyPatch()
    yield monkey_patch
    monkey_patch.undo()


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def db_manager() -> fastapi_mongodb.db.BaseDBManager:
    handler = fastapi_mongodb.db.BaseDBManager(
        db_url="mongodb://0.0.0.0:27017/",
        default_db_name="test_db",
    )
    yield handler
    await handler.delete_database(name="test_db")
    handler.delete_client()


@pytest.fixture(scope="session", autouse=True)
def mongodb_client(monkeypatch_session, db_manager) -> motor.motor_asyncio.AsyncIOMotorClient:
    client = db_manager.retrieve_client()
    monkeypatch_session.setattr(
        target=fastapi_mongodb.db.BaseDBManager, name="retrieve_client", value=lambda *args, **kwargs: client
    )
    db = db_manager.retrieve_database(name="test_db", code_options=fastapi_mongodb.db.CODEC_OPTIONS)
    monkeypatch_session.setattr(
        target=fastapi_mongodb.db.BaseDBManager, name="retrieve_database", value=lambda *args, **kwargs: db
    )
    yield client
    client.close()


@pytest.fixture(scope="session", autouse=True)
def mongodb_db(mongodb_client) -> motor.motor_asyncio.AsyncIOMotorDatabase:
    yield mongodb_client["test_db"]


@pytest.fixture()
async def mongodb_session(mongodb_client) -> motor.motor_asyncio.AsyncIOMotorClientSession:
    async with await mongodb_client.start_session() as session:
        yield session


@pytest.fixture(scope="class")
def repository(db_manager):
    return fastapi_mongodb.repositories.BaseRepository(db_manager=db_manager, db_name="test_db", col_name="test_col")
