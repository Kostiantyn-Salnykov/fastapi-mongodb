import datetime
import typing

import bson
import pydantic.typing
import pymongo.client_session
import pymongo.database
import pymongo.results

import fastapi_mongodb.db
import fastapi_mongodb.helpers
from fastapi_mongodb.config import BaseConfiguration
from fastapi_mongodb.repositories import BaseRepository
from fastapi_mongodb.types import OID


class BaseDBModel(pydantic.BaseModel):
    """Class for MongoDB (class data view)"""

    oid: typing.Optional[OID] = pydantic.Field(alias="_id")

    class Config(BaseConfiguration):
        """configuration class"""

    id = property(fget=lambda self: str(self.oid))

    @classmethod
    def from_db(cls, *, data: dict):
        """Method that using in repositories when converting result from MongoDB"""
        if not data:
            return data
        return cls(**data)

    def dict(
        self,
        *,
        include: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        exclude: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        _to_db: bool = False,
    ) -> "pydantic.typing.DictStrAny":
        if _to_db:
            override_by_alias = True
        else:
            override_by_alias = by_alias  # override value to work with BaseSchema

        return super().dict(
            include=include,
            exclude=exclude,
            by_alias=override_by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def to_db(
        self,
        *,
        include: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        exclude: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,  # pydantic default is False
    ) -> dict:
        """Preparing data for MongoDB"""
        result: dict = self.dict(
            include=include,
            exclude=exclude,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            _to_db=True,
        )

        # if no "oid" and "_id" -> creates it
        if "_id" not in result and "oid" not in result:
            result["_id"] = bson.ObjectId()

        return result


class BaseCreatedUpdatedModel(BaseDBModel):
    created_at: typing.Optional[datetime.datetime] = pydantic.Field(default=None)
    updated_at: typing.Optional[datetime.datetime] = pydantic.Field(default=None)

    def to_db(
        self,
        *,
        include: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        exclude: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,  # pydantic default is False
    ) -> dict:
        result = super(BaseCreatedUpdatedModel, self).to_db(
            include=include,
            exclude=exclude,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        result["updated_at"] = fastapi_mongodb.helpers.utc_now()
        result["created_at"] = result["_id"].generation_time.replace(tzinfo=fastapi_mongodb.helpers.get_utc_timezone())
        return result


class BaseActiveRecord:
    def __init__(self, document: typing.Union[dict, fastapi_mongodb.db.BaseDocument], repository: BaseRepository):
        self._document = document
        self._repository: BaseRepository = repository
        self._unset_data = {}

    def __repr__(self):
        data = f"_id={doc_id}" if (doc_id := self.id) else "NO DOCUMENT _id"
        return f"{self.__class__.__name__}({data})"

    def __setitem__(self, key, value):
        self._document.__setitem__(key, value)
        self._unset_data.pop(key, None)

    def __getitem__(self, item):
        return self._document.__getitem__(item)

    def __delitem__(self, key):
        self._document.__delitem__(key)
        self._unset_data[key] = None

    @property
    def oid(self):
        return self._document.get("_id", None)

    @property
    def id(self):
        return str(self.oid) if self.oid else None

    @property
    def generated_at(self):
        try:
            return self._document["_id"].generation_time.astimezone(tz=fastapi_mongodb.helpers.get_utc_timezone())
        except KeyError as error:
            raise AttributeError("Document has not been created yet!") from error

    def get_collection(self) -> pymongo.collection.Collection:
        return self._repository.col

    def get_db(self) -> pymongo.database.Database:
        return self._repository.db

    @classmethod
    async def create(
        cls, document: dict, repository: BaseRepository, session: pymongo.client_session.ClientSession = None
    ) -> "BaseActiveRecord":
        result = await repository.insert_one(document=document, session=session)
        return await cls.read(query={"_id": result.inserted_id}, repository=repository, session=session)

    @classmethod
    async def insert(
        cls, document: dict, repository: BaseRepository, session: pymongo.client_session.ClientSession = None
    ) -> "BaseActiveRecord":
        return await cls.create(document=document, repository=repository, session=session)

    async def update(self, session: pymongo.client_session.ClientSession = None) -> "BaseActiveRecord":
        updated_document = await self._repository.find_one_and_update(
            query={"_id": self.oid},
            update={"$set": self._document, "$unset": self._unset_data},
            session=session,
        )
        self._document = updated_document
        self._unset_data = {}
        return self

    @classmethod
    async def read(
        cls, query: dict, repository: BaseRepository, session: pymongo.client_session.ClientSession = None
    ) -> "BaseActiveRecord":
        result = await repository.find_one(query=query, session=session)
        return cls(document=result or {}, repository=repository)

    async def delete(self, session: pymongo.client_session.ClientSession = None) -> "BaseActiveRecord":
        await self._repository.delete_one(query={"_id": self.oid}, session=session)
        self._document = {}
        return self

    async def refresh(self, session: pymongo.client_session.ClientSession = None) -> "BaseActiveRecord":
        result = await self._repository.find_one(query={"_id": self.oid}, session=session) if self.oid else None
        self._document = result or {}
        return self

    async def reload(self, session: pymongo.client_session.ClientSession = None) -> "BaseActiveRecord":
        return await self.refresh(session=session)


class NewBaseDataMapper:
    def __init__(
        self,
        repository: BaseRepository,
        model: typing.Type[BaseDBModel],
        db_session: pymongo.client_session.ClientSession = None,
    ):
        self._repository = repository
        self._model = model
        self._db_session = db_session

    @property
    def db_session(self):
        return self._db_session

    @db_session.setter
    def db_session(self, value):
        self._db_session = value

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(repository={self._repository.__class__.__name__}, model={self._model.__name__})"
        )

    async def create(
        self, model: BaseDBModel, raw_result: bool = False, session: pymongo.client_session.ClientSession = None
    ) -> typing.Union[pymongo.results.InsertOneResult, BaseDBModel]:
        session = session or self._db_session
        insertion_result = await self._repository.insert_one(document=model.to_db(), session=session)
        if raw_result:
            return insertion_result
        else:
            return await self.retrieve(query={"_id": insertion_result.inserted_id}, session=session)

    async def list(self, query: dict, session: pymongo.client_session.ClientSession = None):
        return (
            self._model.from_db(data=result)
            async for result in await self._repository.find(query=query, session=session or self._db_session)
        )

    async def retrieve(self, query: dict, session: pymongo.client_session.ClientSession = None):
        document = await self._repository.find_one(query=query, session=session or self._db_session)
        return self._model.from_db(data=document)

    async def partial_update(self, model: BaseDBModel, session: pymongo.client_session.ClientSession = None):
        document = await self._repository.find_one_and_replace(
            query={"_id": model.id}, replacement=model.to_db(), session=session or self._db_session
        )
        return self._model.from_db(data=document)

    async def update(self, model: BaseDBModel, session: pymongo.client_session.ClientSession = None):
        return await self._repository.replace_one(
            query={"_id": model.id}, replacement=model.to_db(), session=session or self._db_session
        )

    async def delete(self, model: BaseDBModel, session: pymongo.client_session.ClientSession = None):
        return await self._repository.delete_one(query={"_id": model.oid}, session=session or self._db_session)
