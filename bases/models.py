import datetime
import typing

import bson
import pydantic

import bases.config
import bases.types
import bases.utils


class BaseMongoDBModel(pydantic.BaseModel):
    """Class for MongoDB (class data view)"""

    id: typing.Optional[bases.types.OID] = pydantic.Field(alias="_id")
    created_datetime: typing.Optional[datetime.datetime] = pydantic.Field(default=None)
    updated_datetime: typing.Optional[datetime.datetime] = pydantic.Field(default=None)

    class Config(bases.config.BaseConfiguration):
        """configuration class"""

        use_datetime_fields: bool = False
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
        if cls.Config.use_datetime_fields:
            data["created_datetime"] = bases.utils.get_naive_datetime_from_object_id(object_id=_id)
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

        # if 'updated_datetime' already exists -> update it by current datetime
        if self.Config.use_datetime_fields:
            result["updated_datetime"] = datetime.datetime.utcnow()

        # replace 'id' to '_id'
        result["_id"] = result.pop("id")
        return result

    @property
    def datetime_created(self):
        """Retrieve created datetime for a document from MongoDB"""
        try:
            return bases.utils.get_naive_datetime_from_object_id(object_id=self.id)
        except (KeyError, AttributeError) as error:
            raise NotImplementedError("You should retrieve an '_id' field from MongoDB to use this property") from error
