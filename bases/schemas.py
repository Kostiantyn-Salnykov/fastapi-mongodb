import datetime
import typing

import pydantic

import bases.config  # noqa
import bases.types


class BaseSchema(pydantic.BaseModel):
    """Class using as a base class for schemas.py"""

    class Config(bases.config.BaseConfiguration):
        """configuration class"""


class CreatedUpdatedBaseSchema(pydantic.BaseModel):
    """Append datetime fields for schema"""

    created_datetime: typing.Optional[datetime.datetime]
    updated_datetime: typing.Optional[datetime.datetime]


class InsertOneResultSchema(BaseSchema):
    acknowledged: bool
    inserted_id: bases.types.OID


class DeleteResultSchema(BaseSchema):
    acknowledged: bool
    deleted_count: int
