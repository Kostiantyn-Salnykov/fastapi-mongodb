import datetime
from typing import Optional, List, Dict, Union

import bson
import orjson
import pydantic
import pymongo
from fastapi import Request, HTTPException, Query, status
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
    "CreatedUpdatedBaseSchema",
    "BasePermission",
    "PermissionsHandler",
    "Paginator",
    "BasePagination",
    "BaseSort",
    "BaseRepository",
]


class OID(str):
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern="^[a-f0-9]{24}$",
            example="5f539e21552f50d572ad66e3",
            title="ObjectId",
            type="string",
        )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            return bson.ObjectId(str(v))
        except bson.errors.InvalidId as e:
            raise ValueError(e)

    def __repr__(self):
        return super().__repr__()


class BaseConfiguration(pydantic.BaseConfig):
    allow_population_by_field_name = True
    use_enum_values = True
    json_encoders = {
        datetime.datetime: lambda dt: dt.timestamp(),
        bson.ObjectId: lambda value: str(value),
    }
    json_dumps = orjson.dumps
    json_loads = orjson.loads


class BaseMongoDBModel(pydantic.BaseModel):
    id: Optional[OID] = pydantic.Field(alias="_id")
    created_datetime: Optional[datetime.datetime]
    updated_datetime: Optional[datetime.datetime]

    class Config(BaseConfiguration):
        pass

    @classmethod
    def from_db(cls, data: dict):
        if not data:
            return data
        _id = data.pop("_id", None)
        return cls(id=_id, created_datetime=_id.generation_time.replace(tzinfo=None), **data)  # noqa

    def to_db(self, **kwargs) -> dict:
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
        try:
            return self.id.generation_time
        except (KeyError, AttributeError):
            raise NotImplementedError("You should retrieve an '_id' field from MongoDB to use this property")


class BaseSchema(pydantic.BaseModel):
    class Config(BaseConfiguration):
        pass


class CreatedUpdatedBaseSchema(pydantic.BaseModel):
    created_datetime: Optional[datetime.datetime]
    updated_datetime: Optional[datetime.datetime]


class BaseRepository:
    def __init__(self, col_name: str, obj_name: str, **kwargs):
        self.obj_name = obj_name
        self._db: Database = get_default_db()
        self.col: Collection = self._db[col_name]
        self._convert_to = kwargs.get("convert_to", None)
        self.convert = kwargs.get("convert", True)
        if not issubclass(self._convert_to, BaseMongoDBModel):
            raise NotImplementedError(f"'convert_to' kwarg must be an subclass from '{BaseMongoDBModel.__name__}'")

    def convert_one_result(self, result: dict, extra_kwargs: dict = None):
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
        extra_kwargs = {} if extra_kwargs is None else extra_kwargs
        raise_not_found = extra_kwargs.get("raise_not_found", True)
        if result is None and raise_not_found:
            raise RepositoryException(detail=f"{self.obj_name} not found", status_code=status.HTTP_404_NOT_FOUND)
        return self.convert_one_result(result=result, extra_kwargs=extra_kwargs)

    async def insert_one(
        self, document: dict, session: ClientSession = None, **kwargs
    ) -> InsertOneResult:
        result: InsertOneResult = await self.col.insert_one(document=document, session=session, **kwargs)
        return result

    async def insert_many(
        self, documents: List[dict], ordered: bool = False, session: ClientSession = None, **kwargs
    ) -> InsertManyResult:
        return await self.col.insert_many(documents=documents, ordered=ordered, session=session, **kwargs)

    async def replace_one(
        self, query: dict, replacement: dict, upsert: bool = False, session: ClientSession = None, **kwargs
    ) -> UpdateResult:
        return await self.col.replace_one(
            filter=query, replacement=replacement, upsert=upsert, session=session, **kwargs
        )

    async def update_one(
        self, query: dict, update: dict, upsert: bool = False, session: ClientSession = None, **kwargs
    ) -> UpdateResult:
        return await self.col.update_one(filter=query, update=update, upsert=upsert, session=session, **kwargs)

    async def update_many(
        self, query: dict, update: dict, upsert: bool = False, session: ClientSession = None, **kwargs
    ) -> UpdateResult:
        return await self.col.update_many(filter=query, update=update, upsert=upsert, session=session, **kwargs)

    async def delete_one(self, query: dict, session: ClientSession = None, **kwargs) -> DeleteResult:
        return await self.col.delete_one(filter=query, session=session, **kwargs)

    async def delete_many(self, query: dict, session: ClientSession = None, **kwargs) -> DeleteResult:
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
        results_cursor = self.col.find(
            filter=query, sort=sort, skip=skip, limit=limit, projection=projection, session=session, **kwargs
        )
        extra_kwargs = {} if extra_kwargs is None else extra_kwargs
        if extra_kwargs.get("convert", self.convert):
            convert_to = extra_kwargs.get("convert_to", self._convert_to)
            return [convert_to.from_db(data=result) async for result in results_cursor]
        else:
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
        result = await self.col.find_one_and_update(
            filter=query, update=update, sort=sort, projection=projection, session=session, **kwargs
        )
        return self._not_found_convert_flow(result=result, extra_kwargs=extra_kwargs)

    async def count_documents(self, query: dict, session: ClientSession = None, **kwargs) -> int:
        return await self.col.count_documents(filter=query, session=session, **kwargs)

    async def estimated_document_count(self, **kwargs):
        return await self.col.estimated_document_count(**kwargs)


class BasePermission:
    def __call__(self, request: Request) -> None:
        """method for available Depends in FastAPI"""
        self.check(request=request)

    def check(self, request: Request):
        raise NotImplementedError


class PermissionsHandler:
    """Class to check list of permissions inside FastAPI Depends"""

    def __init__(self, permissions: List[BasePermission]):
        self.permissions = permissions

    async def __call__(self, request: Request):
        """Class becomes callable that allow to use it inside FastAPI Depends"""
        for permission in self.permissions:
            try:
                permission.check(request=request)
            except PermissionException as exception:
                raise HTTPException(status_code=exception.status_code, detail=exception.detail)


class Paginator(pydantic.BaseModel):
    skip: int = pydantic.Field(
        default=common_settings.PAGINATION_DEFAULT_OFFSET, ge=common_settings.PAGINATION_MIN_OFFSET
    )
    limit: int = pydantic.Field(
        default=common_settings.PAGINATION_DEFAULT_LIMIT,
        ge=common_settings.PAGINATION_MIN_LIMIT,
        le=common_settings.PAGINATION_MAX_LIMIT,
    )


class BasePagination:
    """Base Paginator factory"""

    @staticmethod
    def make_paginator(
        skip: int = common_settings.PAGINATION_DEFAULT_OFFSET, limit: int = common_settings.PAGINATION_DEFAULT_LIMIT
    ) -> Paginator:
        """Method creates and returns Paginator instance by provided arguments"""
        return Paginator(skip=skip, limit=limit)


class BaseSort:
    def __init__(
        self,
        sort_by: Optional[str] = Query(
            default=None,
            max_length=256,
            alias="sortBy",
            description="Comma separated values with 'field_name' for ascending order and '-field_name' for descending "
            "order. Examples: 'sortBy=-email,-id' or 'sortBy=email,id'",
            example="email,-id",
        ),
    ):
        self._default_order = pymongo.ASCENDING
        self._default__id_field = "_id"
        self._default = [(self._default__id_field, self._default_order)]
        self.sort_by = sort_by

    def _parse_sort(self):
        sort_list = self.sort_by.split(",")
        key_or_list = []
        for field in sort_list:
            ordering = self._default_order
            field_value = field
            if field.startswith("-"):
                ordering = pymongo.DESCENDING  # change ordering to descending
                field_value = field[1:]  # get field_value without '-' character

            # convert 'id' field to mongodb '_id'
            if field_value == "id":
                field_value = self._default__id_field

            key_or_list.append((field_value, ordering))

        return key_or_list

    def to_db(self):
        if self.sort_by is None:
            return self._default
        return self._parse_sort()
