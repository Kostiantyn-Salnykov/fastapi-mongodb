import datetime
import typing

import bson
import pydantic

import bases.config
import bases.types
import bases.utils


class BaseCreatedUpdatedModel:
    created_datetime: typing.Optional[datetime.datetime] = pydantic.Field(default=None)
    updated_datetime: typing.Optional[datetime.datetime] = pydantic.Field(default=None)


class BaseMongoDBModel(pydantic.BaseModel):
    """Class for MongoDB (class data view)"""

    id: typing.Optional[bases.types.OID] = pydantic.Field(alias="_id")

    class Config(bases.config.BaseConfiguration):
        """configuration class"""

        sorting_fields: list[str] = []
        sorting_default: str = "-_id"

    @classmethod
    def from_db(cls, data: dict):
        """Method that using in repositories when converting result from MongoDB"""
        if not data:
            return data
        _id = data.pop("_id", None)
        if _id is None:
            return cls(**data)  # projection flow with _id: False
        return cls(id=_id, **data)  # noqa

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

        # if no 'id' -> creates it
        if "id" not in result:
            result["id"] = bson.ObjectId()

        if BaseCreatedUpdatedModel in self.__class__.__bases__:
            result["updated_datetime"] = datetime.datetime.utcnow()
            result["created_datetime"] = result["id"].generation_time.replace(tzinfo=None)

        # replace 'id' to '_id'
        result["_id"] = result.pop("id")
        return result
