"""MongoDB base logic"""
import typing

import bson
import motor.motor_asyncio
import pymongo
import pymongo.client_session
import pymongo.database
import pymongo.errors
import pymongo.monitoring
import pymongo.read_concern

import settings
from bases.logging import logger

__all__ = ["db_handler"]


# TODO (Optimize messages for loggers) kost:
class CommandLogger(pymongo.monitoring.CommandListener):
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


class ConnectionPoolLogger(pymongo.monitoring.ConnectionPoolListener):
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
        logger.debug(
            f"[pool {event.address}][conn #{event.connection_id}] connection closed, reason: {event.reason}"
        )

    def connection_check_out_started(self, event):
        logger.debug(f"[pool {event.address}] connection check out started")

    def connection_check_out_failed(self, event):
        logger.debug(f"[pool {event.address}] connection check out failed, reason: {event.reason}")

    def connection_checked_out(self, event):
        logger.debug(
            f"[pool {event.address}][conn #{event.connection_id}] connection checked out of pool"
        )

    def connection_checked_in(self, event):
        logger.debug(f"[pool {event.address}][conn #{event.connection_id}] connection checked into pool")


class ServerLogger(pymongo.monitoring.ServerListener):
    def opened(self, event):
        logger.debug(f"Server {event.server_address} added to topology {event.topology_id}")

    def description_changed(self, event):
        previous_server_type = event.previous_description.server_type
        new_server_type = event.new_description.server_type
        if new_server_type != previous_server_type:
            logger.debug(
                f"Server {event.server_address} changed type from {event.previous_description.server_type_name} to "
                f"{event.new_description.server_type_name}"
            )

    def closed(self, event):
        logger.debug(f"Server {event.server_address} removed from topology {event.topology_id}")


class HeartbeatLogger(pymongo.monitoring.ServerHeartbeatListener):
    def started(self, event):
        logger.debug(f"Heartbeat sent to server {event.connection_id}")

    def succeeded(self, event):
        logger.debug(
            f"Heartbeat to server {event.connection_id} succeeded with reply {event.reply.document}"
        )

    def failed(self, event):
        logger.debug(f"Heartbeat to server {event.connection_id} failed with error {event.reply}")


class TopologyLogger(pymongo.monitoring.TopologyListener):
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


if settings.Settings.DEBUG:  # pragma: no cover
    if settings.Settings.MONGO_LOGGER_COMMAND:
        pymongo.monitoring.register(listener=CommandLogger())
    if settings.Settings.MONGO_LOGGER_CONNECTION_POOL:
        pymongo.monitoring.register(listener=ConnectionPoolLogger())
    if settings.Settings.MONGO_LOGGER_HEARTBEAT:
        pymongo.monitoring.register(listener=HeartbeatLogger())
    if settings.Settings.MONGO_LOGGER_SERVER:
        pymongo.monitoring.register(listener=ServerLogger())
    if settings.Settings.MONGO_LOGGER_TOPOLOGY:
        pymongo.monitoring.register(listener=TopologyLogger())


class DBHandler:
    """Class hold MongoDB client connection"""

    client: pymongo.MongoClient = None

    @classmethod
    def retrieve_client(cls) -> pymongo.MongoClient:
        """Retrieve existing MongoDB client or create it (at first call)"""
        if cls.client is None:
            logger.debug(msg="Initialization of MongoDB")
            cls.create_client()
        return cls.client

    @classmethod
    def create_client(cls):
        """Creating MongoDB client"""
        logger.debug(msg="Creating MongoDB client")
        cls.client = motor.motor_asyncio.AsyncIOMotorClient(settings.Settings.MONGO_URL)

    @classmethod
    def delete_client(cls):
        """Closing MongoDB client"""
        logger.debug(msg="Disconnecting from MongoDB")
        cls.client.close()
        cls.client = None  # noqa

    @classmethod
    async def get_server_info(cls, *, session: pymongo.client_session.ClientSession = None) -> dict:
        client = cls.retrieve_client()
        return await client.server_info(session=session)

    @classmethod
    def retrieve_database(
        cls,
        *,
        name: str = None,
        code_options: bson.codec_options.CodecOptions = None,
        read_preference: pymongo.ReadPreference = pymongo.ReadPreference.SECONDARY_PREFERRED,  # default None
        write_concern: pymongo.write_concern.WriteConcern = pymongo.write_concern.WriteConcern(
            w="majority", j=True
        ),  # default None
        read_concern: pymongo.read_concern.ReadConcern = pymongo.read_concern.ReadConcern(
            level="majority"
        ),  # default None
    ) -> pymongo.database.Database:
        """Retrieve Database by name"""
        client = cls.retrieve_client()
        if name is None:
            name = settings.Settings.MONGO_DB_NAME
        return client.get_database(
            name=name,
            codec_options=code_options,
            read_preference=read_preference,
            write_concern=write_concern,
            read_concern=read_concern,
        )

    @classmethod
    async def list_databases(
        cls,
        *,
        only_names: bool = False,
        session: pymongo.client_session.ClientSession = None,
    ) -> typing.Union[list[str], list[dict[str, typing.Any]]]:
        client = cls.retrieve_client()
        if only_names:
            return [database for database in await client.list_database_names(session=session)]
        return [database async for database in await client.list_databases(session=session)]

    @classmethod
    async def delete_database(cls, *, name: str, session: pymongo.client_session.ClientSession = None):
        client = cls.retrieve_client()
        await client.drop_database(name_or_database=name, session=session)

    @classmethod
    async def get_profiling_info(cls, *, db_name: str, session: pymongo.client_session.ClientSession = None) -> list:
        database = cls.retrieve_database(name=db_name)
        return await database.profiling_info(session=session)

    @classmethod
    async def get_profiling_level(cls, *, db_name: str, session: pymongo.client_session.ClientSession = None) -> int:
        database = cls.retrieve_database(name=db_name)
        return await database.profiling_level(session=session)

    @classmethod
    async def set_profiling_level(
        cls, *, db_name: str, level, slow_ms: int = None, session: pymongo.client_session.ClientSession = None
    ):
        database = cls.retrieve_database(name=db_name)
        return await database.set_profiling_level(level=level, slow_ms=slow_ms, session=session)

    @classmethod
    async def create_collection(
        cls, *, name: str, db_name: str = None, safe: bool = True, session: pymongo.client_session.ClientSession = None
    ) -> pymongo.collection.Collection:
        """Create collection by name"""
        database = cls.retrieve_database(name=db_name)
        try:
            return await database.create_collection(name=name, session=session)
        except pymongo.errors.CollectionInvalid as error:
            if not safe:
                raise error

    @classmethod
    async def delete_collection(
        cls, *, name: str, db_name: str = None, session: pymongo.client_session.ClientSession = None
    ):
        """Delete collection by name"""
        database = cls.retrieve_database(name=db_name)
        await database.drop_collection(name_or_collection=name, session=session)

    @classmethod
    async def list_collections(
        cls,
        *,
        db_name: str = None,
        only_names: bool = False,
        session: pymongo.client_session.ClientSession = None,
    ) -> typing.Union[list[str], list[dict[str, typing.Any]]]:
        database = cls.retrieve_database(name=db_name)
        if only_names:
            return [collection for collection in await database.list_collection_names(session=session)]
        return [collection for collection in await database.list_collections(session=session)]

    @classmethod
    async def create_index(
        cls,
        *,
        col_name: str,
        db_name: str = None,
        index: list[tuple[str, int]],
        name: str,
        background: bool = True,
        unique: bool = False,
        sparse: bool = False,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> str:
        """Create an index for collection"""
        database = cls.retrieve_database(name=db_name)
        return await database[col_name].create_index(
            keys=index, name=name, background=background, unique=unique, sparse=sparse, session=session, **kwargs
        )

    @classmethod
    async def create_indexes(
        cls,
        *,
        col_name: str,
        indexes: list[pymongo.IndexModel],
        db_name: str = None,
        session: pymongo.client_session.ClientSession = None,
    ):
        """Create indexes for collection by list of IndexModel"""
        database: pymongo.database.Database = cls.retrieve_database(name=db_name)
        return await database[col_name].create_indexes(indexes=indexes, session=session)

    @classmethod
    async def delete_index(
        cls,
        *,
        name: str,
        col_name: str,
        db_name: str = None,
        safe: bool = True,
        session: pymongo.client_session.ClientSession = None,
    ):
        database = cls.retrieve_database(name=db_name)
        try:
            await database[col_name].drop_index(index_or_name=name, session=session)
        except pymongo.errors.OperationFailure as error:
            if not safe:
                raise error

    @classmethod
    async def list_indexes(
        cls,
        *,
        col_name: str,
        db_name: str = None,
        only_names: bool = False,
        session: pymongo.client_session.ClientSession = None,
    ):
        database = cls.retrieve_database(name=db_name)
        if only_names:
            return [index["name"] async for index in database[col_name].list_indexes(session=session)]
        return [index async for index in database[col_name].list_indexes(session=session)]


db_handler = DBHandler()
