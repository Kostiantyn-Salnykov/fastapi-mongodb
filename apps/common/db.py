import logging
from typing import List, Tuple

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.client_session import ClientSession
from pymongo.database import Database
from pymongo.errors import CollectionInvalid

from settings import settings

logger = logging.getLogger("uvicorn")

__all__ = [
    "create_mongo_connection",
    "close_mongo_connection",
    "get_default_db",
    "get_mongo_client",
    "make_index",
    "make_indexes",
    "make_collection",
]


class MongoDBConnection:
    client: AsyncIOMotorClient = None


mongo_connection = MongoDBConnection()


def get_mongo_client() -> AsyncIOMotorClient:
    if mongo_connection is None or not hasattr(mongo_connection, "client") or not mongo_connection.client:
        create_mongo_connection()
    return mongo_connection.client


def create_mongo_connection():
    logger.info(msg="Connecting to MongoDB client")
    mongo_connection.client = AsyncIOMotorClient(settings.MONGO_URL)


def close_mongo_connection():
    logger.info(msg="Disconnecting from MongoDB")
    mongo_connection.client.close()


def get_default_db() -> Database:
    client = get_mongo_client()
    return client.get_database(name=settings.MONGO_DB_NAME, read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED)


def get_db_by_name(name: str) -> Database:
    client = get_mongo_client()
    return client.get_database(name=name, read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED)


async def make_collection(col_name: str, raise_on_exists: bool = False, session: ClientSession = None):
    db = get_default_db()
    try:
        await db.create_collection(name=col_name, session=session)
    except CollectionInvalid as error:
        if raise_on_exists:
            raise error


async def make_index(
    col_name: str,
    index: List[Tuple[str, int]],
    name: str,
    background: bool = True,
    unique: bool = False,
    session: ClientSession = None,
):
    db = get_default_db()
    result = await db[col_name].create_index(
        keys=index, name=name, background=background, unique=unique, session=session
    )
    return result


async def make_indexes(
    col_name: str,
    indexes: List[pymongo.IndexModel],
    session: ClientSession = None,
):
    db = get_default_db()
    result = await db[col_name].create_indexes(indexes=indexes, session=session)
    return result
