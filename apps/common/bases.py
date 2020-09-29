"""Bases classes for project"""
import datetime
from typing import Optional, List, Dict, Union

import bson
import fastapi
import orjson
import pydantic
import pymongo
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import InsertOneResult, InsertManyResult, UpdateResult, DeleteResult

from apps.common.config import common_settings
from apps.common.db import get_default_db
from apps.common.exceptions import PermissionException, RepositoryException

__all__ = [
    "OID",
    "BaseMongoDBModel",
    "BaseSchema",
    "BasePermission",
    "PermissionsHandler",
    "Paginator",
    "BaseSort",
    "BaseRepository",
]


class OID(str):
    """ObjectId type for BaseMongoDBModels and BaseSchemas"""

    @classmethod
    def __modify_schema__(cls, field_schema):
        """Update OpenAPI docs schema"""
        field_schema.update(
            pattern="^[a-f0-9]{24}$",
            example="5f539e21552f50d572ad66e3",
            title="ObjectId",
            type="string",
        )

    @classmethod
    def __get_validators__(cls):
        """Default method for Pydantic Types"""
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """Default validation for Pydantic Types"""
        try:
            return bson.ObjectId(str(v))
        except bson.errors.InvalidId as error:
            raise ValueError(error) from error


class BaseConfiguration(pydantic.BaseConfig):
    """base configuration class for Models and Schemas"""

    allow_population_by_field_name = True
    use_enum_values = True
    json_encoders = {
        datetime.datetime: lambda dt: dt.timestamp(),
        bson.ObjectId: str,
    }
    json_dumps = orjson.dumps
    json_loads = orjson.loads


class BaseMongoDBModel(pydantic.BaseModel):
    """Class for MongoDB (class data view)"""

    id: Optional[OID] = pydantic.Field(alias="_id")
    created_datetime: Optional[datetime.datetime]
    updated_datetime: Optional[datetime.datetime]

    class Config(BaseConfiguration):
        """configuration class"""

        sorting_fields: List[str] = []
        sorting_default: str = "-_id"

    @classmethod
    def from_db(cls, data: dict):
        """Method that using in repositories when converting result from MongoDB"""
        if not data:
            return data
        _id = data.pop("_id", None)
        return cls(id=_id, created_datetime=_id.generation_time.replace(tzinfo=None), **data)  # noqa

    def to_db(self, **kwargs) -> dict:
        """Preparing data for MongoDB"""
        exclude_none = kwargs.pop("exclude_none", True)
        by_alias = kwargs.pop("by_alias", True)

        result: dict = self.dict(exclude_none=exclude_none, by_alias=by_alias, **kwargs)

        # if no 'id' -> creates it
        if "id" not in result:
            result["id"] = bson.ObjectId()

        # if 'updated_datetime' already exists -> update it by current datetime
        if "updated_datetime" in result:
            result["updated_datetime"] = datetime.datetime.utcnow()

        # if 'id' exists and no 'updated_datetime' -> get it from ObjectId
        if "id" in result and "updated_datetime" not in result:
            result["updated_datetime"] = result["id"].generation_time.replace(tzinfo=None)

        # replace 'id' to '_id'
        if "_id" not in result and "id" in result:
            result["_id"] = result.pop("id")

        return result

    @property
    def datetime_created(self):
        """Retrieve created datetime for document from MongoDB"""
        try:
            return self.id.generation_time.replace(tzinfo=None)
        except (KeyError, AttributeError) as error:
            raise NotImplementedError("You should retrieve an '_id' field from MongoDB to use this property") from error


class BaseSchema(pydantic.BaseModel):
    """Class that using as a base class for schemas.py"""

    class Config(BaseConfiguration):
        """configuration class"""


class BaseRepository:
    """Class for CRUD for MongoDB"""

    def __init__(self, col_name: str, obj_name: str, **kwargs):
        self.obj_name = obj_name
        self._db: Database = get_default_db()
        self.col: Collection = self._db[col_name]
        self._convert_to = kwargs.get("convert_to", None)
        self.convert = kwargs.get("convert", True)
        if not issubclass(self._convert_to, BaseMongoDBModel):
            raise NotImplementedError(f"'convert_to' kwarg must be an subclass from '{BaseMongoDBModel.__name__}'")

    def convert_one_result(self, result: dict, extra_kwargs: dict = None):
        """Convert result from MongoDB to BaseMongoDBModel subclass"""
        extra_kwargs = {} if extra_kwargs is None else extra_kwargs
        if extra_kwargs.get("convert", self.convert):
            convert_to = extra_kwargs.get("convert_to", self._convert_to)
            if convert_to is None:
                raise NotImplementedError(
                    "Please setup repository class (append 'convert_to' argument) or pass 'convert=False' to this "
                    "method call."
                )
            result = convert_to.from_db(data=result)
        return result

    def _not_found_convert_flow(self, result, extra_kwargs: dict = None):
        """convert result to BaseMongoDBModel subclass or raise error if result is None"""
        extra_kwargs = {} if extra_kwargs is None else extra_kwargs
        raise_not_found = extra_kwargs.get("raise_not_found", True)
        if result is None and raise_not_found:
            raise RepositoryException(
                detail=f"{self.obj_name} not found", status_code=fastapi.status.HTTP_404_NOT_FOUND
            )
        return self.convert_one_result(result=result, extra_kwargs=extra_kwargs)

    async def insert_one(self, document: dict, session: ClientSession = None, **kwargs) -> InsertOneResult:
        """insert one document to MongoDB"""
        result: InsertOneResult = await self.col.insert_one(document=document, session=session, **kwargs)
        return result

    async def insert_many(
        self, documents: List[dict], ordered: bool = False, session: ClientSession = None, **kwargs
    ) -> InsertManyResult:
        """insert many documents to MongoDB"""
        return await self.col.insert_many(documents=documents, ordered=ordered, session=session, **kwargs)

    async def replace_one(
        self, query: dict, replacement: dict, upsert: bool = False, session: ClientSession = None, **kwargs
    ) -> UpdateResult:
        """replace one document in MongoDB"""
        return await self.col.replace_one(
            filter=query, replacement=replacement, upsert=upsert, session=session, **kwargs
        )

    async def update_one(
        self, query: dict, update: dict, upsert: bool = False, session: ClientSession = None, **kwargs
    ) -> UpdateResult:
        """update one document to MongoDB"""
        return await self.col.update_one(filter=query, update=update, upsert=upsert, session=session, **kwargs)

    async def update_many(
        self, query: dict, update: dict, upsert: bool = False, session: ClientSession = None, **kwargs
    ) -> UpdateResult:
        """update many documents to MongoDB"""
        return await self.col.update_many(filter=query, update=update, upsert=upsert, session=session, **kwargs)

    async def delete_one(self, query: dict, session: ClientSession = None, **kwargs) -> DeleteResult:
        """delete one document from MongoDB"""
        return await self.col.delete_one(filter=query, session=session, **kwargs)

    async def delete_many(self, query: dict, session: ClientSession = None, **kwargs) -> DeleteResult:
        """delete many document from MongoDB"""
        return await self.col.delete_many(filter=query, session=session, **kwargs)

    async def find(
        self,
        query: dict,
        sort: List[tuple] = None,
        skip: int = 0,
        limit: int = 0,
        projection: Union[List[str], Dict[str, bool]] = None,
        session: ClientSession = None,
        extra_kwargs: dict = None,
        **kwargs,
    ):
        """find documents from MongoDB"""
        results_cursor = self.col.find(
            filter=query, sort=sort, skip=skip, limit=limit, projection=projection, session=session, **kwargs
        )
        extra_kwargs = {} if extra_kwargs is None else extra_kwargs
        if extra_kwargs.get("convert", self.convert):
            convert_to = extra_kwargs.get("convert_to", self._convert_to)
            return [convert_to.from_db(data=result) async for result in results_cursor]
        return [result async for result in results_cursor]

    async def find_one(
        self,
        query: dict,
        sort: List[tuple] = None,
        projection: Union[List[str], Dict[str, bool]] = None,
        session: ClientSession = None,
        extra_kwargs: dict = None,
        **kwargs,
    ):
        """find one document from MongoDB"""
        result = await self.col.find_one(filter=query, sort=sort, projection=projection, session=session, **kwargs)
        return self._not_found_convert_flow(result=result, extra_kwargs=extra_kwargs)

    async def find_one_and_delete(
        self,
        query: dict,
        sort: List[tuple] = None,
        projection: Union[List[str], Dict[str, bool]] = None,
        session: ClientSession = None,
        extra_kwargs: dict = None,
        **kwargs,
    ):
        """find one and delete document from MongoDB"""
        result = await self.col.find_one_and_delete(
            filter=query, projection=projection, sort=sort, session=session, **kwargs
        )
        return self._not_found_convert_flow(result=result, extra_kwargs=extra_kwargs)

    async def find_one_and_replace(
        self,
        query: dict,
        replacement: dict,
        upsert: bool = False,
        sort: List[tuple] = None,
        projection: Union[List[str], Dict[str, bool]] = None,
        session: ClientSession = None,
        extra_kwargs: dict = None,
        **kwargs,
    ):
        """find one and replace document from MongoDB"""
        result = await self.col.find_one_and_replace(
            filter=query,
            replacement=replacement,
            upsert=upsert,
            sort=sort,
            projection=projection,
            session=session,
            **kwargs,
        )
        return self._not_found_convert_flow(result=result, extra_kwargs=extra_kwargs)

    async def find_one_and_update(
        self,
        query: dict,
        update: dict,
        sort: List[tuple] = None,
        projection: Union[List[str], Dict[str, bool]] = None,
        session: ClientSession = None,
        extra_kwargs: dict = None,
        **kwargs,
    ):
        """find one and update document from MongoDB"""
        result = await self.col.find_one_and_update(
            filter=query, update=update, sort=sort, projection=projection, session=session, **kwargs
        )
        return self._not_found_convert_flow(result=result, extra_kwargs=extra_kwargs)

    async def count_documents(self, query: dict, session: ClientSession = None, **kwargs) -> int:
        """count documents in MongoDB collection"""
        return await self.col.count_documents(filter=query, session=session, **kwargs)

    async def estimated_document_count(self, **kwargs):
        """count documents in MongoDB from collection metadata"""
        return await self.col.estimated_document_count(**kwargs)


class BasePermission:
    """Class for permission implementation"""

    def __call__(self, request: fastapi.Request) -> None:
        """method for available Depends in FastAPI"""
        self.check(request=request)

    def check(self, request: fastapi.Request):
        """default method for check permission"""
        raise NotImplementedError


class PermissionsHandler:
    """Class to check list of permissions inside FastAPI Depends"""

    def __init__(self, permissions: List[BasePermission]):
        self.permissions = permissions

    async def __call__(self, request: fastapi.Request):
        """Class becomes callable that allow to use it inside FastAPI Depends"""
        for permission in self.permissions:
            try:
                permission.check(request=request)
            except PermissionException as exception:
                raise fastapi.HTTPException(status_code=exception.status_code, detail=exception.detail) from exception


class Paginator(pydantic.BaseModel):
    """Class that returns from pagination"""

    skip: int = pydantic.Field(
        default=common_settings.PAGINATION_DEFAULT_OFFSET, ge=common_settings.PAGINATION_MIN_OFFSET
    )
    limit: int = pydantic.Field(
        default=common_settings.PAGINATION_DEFAULT_LIMIT,
        ge=common_settings.PAGINATION_MIN_LIMIT,
        le=common_settings.PAGINATION_MAX_LIMIT,
    )


class BaseSort:
    """Class as dependency for sorting query system"""

    def __init__(self, model: BaseMongoDBModel, default_sort_query: str = "-_id"):
        self.model = model
        self.default_sort_query = default_sort_query
        self.sorting_model_fields: List[str] = self._get_sorting_fields()
        self.sorting_model_default: str = self._get_sorting_default()
        self.order_by = None

    def __call__(
        self,
        order_by: Optional[str] = fastapi.Query(
            default=None,
            max_length=256,
            alias="orderBy",
            description="Comma separated values with 'field_name' for ascending order and '-field_name' for descending "
            "order. Examples: 'sortBy=-email,-id' or 'sortBy=email,id'",
            example="email,-id",
        ),
    ):
        if order_by is None:
            self.order_by = self.sorting_model_default
        else:
            self.order_by = order_by
        return self

    def _get_sorting_fields(self):
        try:
            return self.model.Config.sorting_fields
        except Exception as error:
            raise NotImplementedError from error

    def _get_sorting_default(self):
        try:
            return self.model.Config.sorting_default
        except (KeyError, AttributeError):
            return self.default_sort_query

    def to_db(self):
        """Collect sorting keys for MongoDB"""
        sort_list = self.order_by.split(",")
        key_or_list = []
        for field in sort_list:
            ordering = pymongo.ASCENDING
            field_value = field
            if field.startswith("-"):
                ordering = pymongo.DESCENDING  # change ordering to descending
                field_value = field[1:]  # get field_value without '-' character

            # convert 'id' field to mongodb '_id'
            if field_value == "id":
                field_value = "_id"

            if field_value in self.sorting_model_fields:
                key_or_list.append((field_value, ordering))

        key_or_list.sort()
        return key_or_list
