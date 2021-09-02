"""MongoDB base logic"""
import collections.abc
import datetime
import decimal
import re
import typing

import bson
import motor.motor_asyncio
import pydantic.json
import pymongo
import pymongo.client_session
import pymongo.database
import pymongo.errors
import pymongo.monitoring
import pymongo.read_concern
from bson import UuidRepresentation

import fastapi_mongodb.helpers
from fastapi_mongodb.logging import simple_logger as logger

__all__ = [
    "CommandLogger",
    "ConnectionPoolLogger",
    "BaseDBManager",
    "HeartbeatLogger",
    "ServerLogger",
    "TopologyLogger",
    "BaseDocument",
    "DECIMAL_CODEC",
    "TIMEDELTA_CODEC",
    "CODEC_OPTIONS",
]


class BaseDocument(collections.abc.MutableMapping):
    def __init__(self, data: dict = None):
        self._data = data or {}

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        return self._data.__getitem__(item)

    def __setitem__(self, key, value):
        return self._data.__setitem__(key, value)

    def __delitem__(self, key):
        return self._data.__delitem__(key)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        data = f"_id={doc_id}" if (doc_id := self.id) else "NO DOCUMENT _id"
        return f"{self.__class__.__name__}({data})"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.data == other.data
        elif isinstance(other, dict):
            return self.data == other
        else:
            return False

    @property
    def data(self) -> dict[str, typing.Any]:
        return self._data

    @property
    def oid(self) -> bson.ObjectId:
        return self._data.get("_id", None)

    @property
    def id(self) -> str:
        return str(self.oid) if self.oid else None

    @property
    def generated_at(self):
        return self.oid.generation_time.astimezone(tz=fastapi_mongodb.helpers.get_utc_timezone())


class DecimalCodec(bson.codec_options.TypeCodec):
    python_type = decimal.Decimal
    bson_type = bson.Decimal128

    def transform_python(self, value):
        return bson.Decimal128(value=value)

    def transform_bson(self, value):
        return value.to_decimal()


class TimeDeltaCodec(bson.codec_options.TypeCodec):
    python_type = datetime.timedelta
    bson_type = bson.string_type

    def transform_python(self, value):
        return pydantic.json.timedelta_isoformat(value)

    def transform_bson(self, value):
        def get_iso_split(s, split):
            if split in s:
                n, s = s.split(split)
            else:
                n = 0
            return n, s

        def get_int(s):
            try:
                return int(s)
            except ValueError:
                return 0

        def parse_iso_duration(string: str) -> typing.Union[str, datetime.timedelta]:
            valid_duration = re.match(
                pattern=r"^P(?!$)((\d+Y)|(\d+\.\d+Y$))?((\d+M)|(\d+\.\d+M$))?((\d+W)|(\d+\.\d+W$))?((\d+D)|"
                r"(\d+\.\d+D$))?(T(?=\d)((\d+H)|(\d+\.\d+H$))?((\d+M)|(\d+\.\d+M$))?(\d+(\.\d+)?S)?)??$",
                string=string,
            )
            if not valid_duration:
                return string
            # Remove prefix
            s = string.removeprefix("P")
            # Step through letter dividers
            weeks, s = get_iso_split(s, "W")
            days, s = get_iso_split(s, "D")
            _, s = get_iso_split(s, "T")
            hours, s = get_iso_split(s, "H")
            minutes, s = get_iso_split(s, "M")
            full_seconds, s = get_iso_split(s, "S")
            secs, _, micros = full_seconds.partition(".")
            seconds = get_int(secs)
            microseconds = get_int(micros)
            return datetime.timedelta(
                weeks=int(weeks),
                days=int(days),
                hours=int(hours),
                minutes=int(minutes),
                seconds=seconds,
                microseconds=microseconds,
            )

        return parse_iso_duration(string=value)


DECIMAL_CODEC = DecimalCodec()
TIMEDELTA_CODEC = TimeDeltaCodec()

CODEC_OPTIONS = bson.codec_options.CodecOptions(
    document_class=BaseDocument,
    uuid_representation=UuidRepresentation.STANDARD,
    tz_aware=True,
    tzinfo=fastapi_mongodb.helpers.get_utc_timezone(),
    type_registry=bson.codec_options.TypeRegistry(type_codecs=[DECIMAL_CODEC, TIMEDELTA_CODEC]),
)


# TODO: Make loggers customizable
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
        logger.debug(f"[pool {event.address}][conn #{event.connection_id}] connection closed, reason: {event.reason}")

    def connection_check_out_started(self, event):
        logger.debug(f"[pool {event.address}] connection check out started")

    def connection_check_out_failed(self, event):
        logger.debug(f"[pool {event.address}] connection check out failed, reason: {event.reason}")

    def connection_checked_out(self, event):
        logger.debug(f"[pool {event.address}][conn #{event.connection_id}] connection checked out of pool")

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
        logger.debug(f"Heartbeat to server {event.connection_id} succeeded with reply {event.reply.document}")

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


class BaseDBManager:
    """Class hold MongoDB client connection"""

    client: pymongo.MongoClient = None

    def __init__(
        self, db_url: str, default_db_name: str = "main", code_options: bson.codec_options.CodecOptions = CODEC_OPTIONS
    ):
        self.db_url = db_url
        self.default_db_name = default_db_name
        self.codec_options = code_options

    def retrieve_client(self) -> pymongo.MongoClient:
        """Retrieve existing MongoDB client or create it (at first call)"""
        if self.__class__.client is None:  # pragma: no cover
            logger.debug(msg="Initialization of MongoDB")
            self.create_client()
        return self.__class__.client

    def create_client(self):
        """Creating MongoDB client"""
        logger.debug(msg="Creating MongoDB client")
        self.__class__.client = motor.motor_asyncio.AsyncIOMotorClient(self.db_url)

    def delete_client(self):
        """Closing MongoDB client"""
        logger.debug(msg="Disconnecting from MongoDB")
        self.__class__.client.close()
        self.__class__.client = None  # noqa

    async def get_server_info(self, *, session: pymongo.client_session.ClientSession = None) -> dict:
        client = self.retrieve_client()
        return await client.server_info(session=session)

    def retrieve_database(
        self,
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
        client = self.retrieve_client()
        if name is None:  # pragma: no cover
            name = self.default_db_name
        if code_options is None:  # pragma: no cover
            code_options = self.codec_options
        return client.get_database(
            name=name,
            codec_options=code_options,
            read_preference=read_preference,
            write_concern=write_concern,
            read_concern=read_concern,
        )

    async def list_databases(
        self,
        *,
        only_names: bool = False,
        session: pymongo.client_session.ClientSession = None,
    ) -> typing.Union[list[str], list[dict[str, typing.Any]]]:
        client = self.retrieve_client()
        if only_names:
            return [database for database in await client.list_database_names(session=session)]
        return [database async for database in await client.list_databases(session=session)]

    async def delete_database(self, *, name: str, session: pymongo.client_session.ClientSession = None):
        client = self.retrieve_client()
        await client.drop_database(name_or_database=name, session=session)

    async def get_profiling_info(self, *, db_name: str, session: pymongo.client_session.ClientSession = None) -> list:
        database = self.retrieve_database(name=db_name)
        return [item async for item in database["system.profile"].find(session=session)]

    async def get_profiling_level(self, *, db_name: str, session: pymongo.client_session.ClientSession = None) -> int:
        database = self.retrieve_database(name=db_name)
        result = await database.command("profile", -1, session=session)
        return result["was"]

    async def set_profiling_level(
        self, *, db_name: str, level, slow_ms: int = None, session: pymongo.client_session.ClientSession = None
    ):
        database = self.retrieve_database(name=db_name)
        return await database.command("profile", level, slowms=slow_ms, session=session)

    async def create_collection(
        self, *, name: str, db_name: str = None, safe: bool = True, session: pymongo.client_session.ClientSession = None
    ) -> pymongo.collection.Collection:
        """Create collection by name"""
        database = self.retrieve_database(name=db_name)
        try:
            return await database.create_collection(name=name, session=session)
        except pymongo.errors.CollectionInvalid as error:
            if not safe:
                raise error

    async def delete_collection(
        self, *, name: str, db_name: str = None, session: pymongo.client_session.ClientSession = None
    ):
        """Delete collection by name"""
        database = self.retrieve_database(name=db_name)
        await database.drop_collection(name_or_collection=name, session=session)

    async def list_collections(
        self,
        *,
        db_name: str = None,
        only_names: bool = False,
        session: pymongo.client_session.ClientSession = None,
    ) -> typing.Union[list[str], list[dict[str, typing.Any]]]:
        database = self.retrieve_database(name=db_name)
        if only_names:
            return [collection for collection in await database.list_collection_names(session=session)]
        return [collection for collection in await database.list_collections(session=session)]

    async def create_index(
        self,
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
        database = self.retrieve_database(name=db_name)
        return await database[col_name].create_index(
            keys=index, name=name, background=background, unique=unique, sparse=sparse, session=session, **kwargs
        )

    async def create_indexes(
        self,
        *,
        col_name: str,
        indexes: list[pymongo.IndexModel],
        db_name: str = None,
        session: pymongo.client_session.ClientSession = None,
    ):
        """Create indexes for collection by list of IndexModel"""
        database: pymongo.database.Database = self.retrieve_database(name=db_name)
        return await database[col_name].create_indexes(indexes=indexes, session=session)

    async def delete_index(
        self,
        *,
        name: str,
        col_name: str,
        db_name: str = None,
        safe: bool = True,
        session: pymongo.client_session.ClientSession = None,
    ):
        database = self.retrieve_database(name=db_name)
        try:
            await database[col_name].drop_index(index_or_name=name, session=session)
        except pymongo.errors.OperationFailure as error:
            if not safe:
                raise error

    async def list_indexes(
        self,
        *,
        col_name: str,
        db_name: str = None,
        only_names: bool = False,
        session: pymongo.client_session.ClientSession = None,
    ):
        database = self.retrieve_database(name=db_name)
        if only_names:
            return [index["name"] async for index in database[col_name].list_indexes(session=session)]
        return [index async for index in database[col_name].list_indexes(session=session)]
