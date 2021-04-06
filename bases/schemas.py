import datetime
import typing

import pydantic

from bases.config import BaseConfiguration
from bases.types import OID


class BaseSchema(pydantic.BaseModel):
    """Class using as a base class for schemas.py"""

    class Config(BaseConfiguration):
        """configuration class"""


class CreatedUpdatedBaseSchema(pydantic.BaseModel):
    """Append datetime fields for schema"""

    created_datetime: typing.Optional[datetime.datetime]
    updated_datetime: typing.Optional[datetime.datetime]


class InsertOneResultSchema(BaseSchema):
    """Insertion result from MongoDB"""

    acknowledged: bool
    inserted_id: OID


class DeleteResultSchema(BaseSchema):
    """Delete result from MongoDB"""

    acknowledged: bool
    deleted_count: int
