import datetime
import typing

import bson
import pydantic
import pymongo

from fastapi_mongodb.config import BaseConfiguration
from fastapi_mongodb.types import OID


class BaseDBModel(pydantic.BaseModel):
    """Class for MongoDB (class data view)"""

    id: typing.Optional[OID] = pydantic.Field(alias="_id")

    class Config(BaseConfiguration):
        """configuration class"""

        sorting_fields: list[str] = []
        sorting_default: list[tuple[str, int]] = [("_id", pymongo.DESCENDING)]

    @classmethod
    def from_db(cls, *, data: dict):
        """Method that using in repositories when converting result from MongoDB"""
        if not data:
            return data
        return cls(**data)

    def to_db(
        self,
        *,
        include: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        exclude: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        by_alias: bool = True,  # pydantic default is False
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,  # pydantic default is False
    ) -> dict:
        """Preparing data for MongoDB"""

        result: dict = self.dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

        # if no "id" and "_id" -> creates it
        if "_id" not in result and "id" not in result:
            result["_id"] = bson.ObjectId()

        if "_id" not in result and "id" in result:
            # replace "id" to "_id"
            result["_id"] = result.pop("id")

        return result


class BaseCreatedUpdatedModel(BaseDBModel):
    created_at: typing.Optional[datetime.datetime] = pydantic.Field(default=None)
    updated_at: typing.Optional[datetime.datetime] = pydantic.Field(default=None)

    def to_db(
        self,
        *,
        include: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        exclude: typing.Union["pydantic.typing.AbstractSetIntStr", "pydantic.typing.MappingIntStrAny"] = None,
        by_alias: bool = True,  # pydantic default is False
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,  # pydantic default is False
    ) -> dict:
        result = super(BaseCreatedUpdatedModel, self).to_db(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none
        )
        result["updated_at"] = datetime.datetime.now(tz=datetime.timezone.utc)
        result["created_at"] = result["_id"].generation_time.replace(tzinfo=datetime.timezone.utc)
        return result
