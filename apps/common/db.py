"""MongoDB base logic"""
from typing import List, Tuple

import pymongo
from pymongo import monitoring
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.client_session import ClientSession
from pymongo.database import Database
from pymongo.errors import CollectionInvalid

from apps.common.logging import logger
from settings import settings


__all__ = [
    "create_mongo_connection",
    "close_mongo_connection",
    "get_default_db",
    "get_mongo_client",
    "make_index",
    "make_indexes",
    "make_collection",
]


class CommandLogger(monitoring.CommandListener):
    def started(self, event):
        logger.debug(
            f"Command '{event.command_name}' with request id {event.request_id} started on server {event.connection_id}"
        )

    def succeeded(self, event):
        logger.debug(
            f"Command '{event.command_name}' with request id {event.request_id} on server {event.connection_id} "
            f"succeeded in {event.duration_micros} microseconds"
        )

    def failed(self, event):
        logger.debug(
            f"Command {event.command_name} with request id {event.request_id} on server {event.connection_id} failed "
            f"in {event.duration_micros} microseconds"
        )


class ConnectionPoolLogger(monitoring.ConnectionPoolListener):
    def pool_created(self, event):
        logger.debug(f"[pool {event.address}] pool created")

    def pool_cleared(self, event):
        logger.debug(f"[pool {event.address}] pool cleared")

    def pool_closed(self, event):
        logger.debug(f"[pool {event.address}] pool closed")

    def connection_created(self, event):
        logger.debug(f"[pool {event.address}][conn #{event.connection_id}] connection created")

    def connection_ready(self, event):
        logger.debug(f"[pool {event.address}][conn #{event.connection_id}] connection setup succeeded")

    def connection_closed(self, event):
        logger.debug(f"[pool {event.address}][conn #{event.connection_id}] connection closed, reason: {event.reason}")

    def connection_check_out_started(self, event):
        logger.debug(f"[pool {event.address}] connection check out started")

    def connection_check_out_failed(self, event):
        logger.debug(f"[pool {event.address}] connection check out failed, reason: {event.reason}")

    def connection_checked_out(self, event):
        logger.debug(f"[pool {event.address}][conn #{event.connection_id}] connection checked out of pool")

    def connection_checked_in(self, event):
        logger.debug(f"[pool {event.address}][conn #{event.connection_id}] connection checked into pool")


class ServerLogger(monitoring.ServerListener):
    def opened(self, event):
        logger.debug(f"Server {event.server_address} added to topology {event.topology_id}")

    def description_changed(self, event):
        previous_server_type = event.previous_description.server_type
        new_server_type = event.new_description.server_type
        if new_server_type != previous_server_type:
            # server_type_name was added in PyMongo 3.4
            logger.debug(
                f"Server {event.server_address} changed type from {event.previous_description.server_type_name} to "
                f"{event.new_description.server_type_name}"
            )

    def closed(self, event):
        logger.debug(f"Server {event.server_address} removed from topology {event.topology_id}")


class HeartbeatLogger(monitoring.ServerHeartbeatListener):
    def started(self, event):
        logger.debug(f"Heartbeat sent to server {event.connection_id}")

    def succeeded(self, event):
        logger.debug(f"Heartbeat to server {event.connection_id} succeeded with reply {event.reply.document}")

    def failed(self, event):
        logger.debug(f"Heartbeat to server {event.connection_id} failed with error {event.reply}")


class TopologyLogger(monitoring.TopologyListener):
    def opened(self, event):
        logger.debug(f"Topology with id {event.topology_id} opened")

    def description_changed(self, event):
        logger.debug(f"Topology description updated for topology id {event.topology_id}")
        previous_topology_type = event.previous_description.topology_type
        new_topology_type = event.new_description.topology_type
        if new_topology_type != previous_topology_type:
            logger.debug(
                f"Topology {event.topology_id} changed type from {event.previous_description.topology_type_name} to "
                f"{event.new_description.topology_type_name}"
            )
        if not event.new_description.has_writable_server():
            logger.debug("No writable servers available.")
        if not event.new_description.has_readable_server():
            logger.debug("No readable servers available.")

    def closed(self, event):
        logger.debug(f"Topology with id {event.topology_id} closed")


if settings.DEBUG:
    if settings.MONGO_LOGGER_COMMAND:
        monitoring.register(listener=CommandLogger())
    if settings.MONGO_LOGGER_CONNECTION_POOL:
        monitoring.register(listener=ConnectionPoolLogger())
    if settings.MONGO_LOGGER_HEARTBEAT:
        monitoring.register(listener=HeartbeatLogger())
    if settings.MONGO_LOGGER_SERVER:
        monitoring.register(listener=ServerLogger())
    if settings.MONGO_LOGGER_TOPOLOGY:
        monitoring.register(listener=TopologyLogger())


class MongoDBConnection:
    """Class that hold MongoDB client connection"""

    client: AsyncIOMotorClient = None


mongo_connection = MongoDBConnection()


def get_mongo_client() -> AsyncIOMotorClient:
    """Retrieve existing MongoDB client or create it (at first call)"""
    if mongo_connection is None or not hasattr(mongo_connection, "client") or not mongo_connection.client:
        create_mongo_connection()
    return mongo_connection.client


def create_mongo_connection():
    """Creating MongoDB client"""
    logger.info(msg="Connecting to MongoDB client")
    mongo_connection.client = AsyncIOMotorClient(settings.MONGO_URL)


def close_mongo_connection():
    """Closing MongoDB client"""
    logger.info(msg="Disconnecting from MongoDB")
    mongo_connection.client.close()


def get_default_db() -> Database:
    """Retrieve default Database"""
    client = get_mongo_client()
    return client.get_database(name=settings.MONGO_DB_NAME, read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED)


def get_db_by_name(name: str) -> Database:
    """Retrieve Database by name"""
    client = get_mongo_client()
    return client.get_database(name=name, read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED)


async def make_collection(col_name: str, raise_on_exists: bool = False, session: ClientSession = None):
    """Create collection by """
    database = get_default_db()
    try:
        await database.create_collection(name=col_name, session=session)
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
    """Create index for collection"""
    database = get_default_db()
    result = await database[col_name].create_index(
        keys=index, name=name, background=background, unique=unique, session=session
    )
    return result


async def make_indexes(
    col_name: str,
    indexes: List[pymongo.IndexModel],
    session: ClientSession = None,
):
    """Create indexes for collection by list of IndexModel"""
    database = get_default_db()
    result = await database[col_name].create_indexes(indexes=indexes, session=session)
    return result
