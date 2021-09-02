import datetime
import typing

import pydantic

from fastapi_mongodb.config import BaseConfiguration
from fastapi_mongodb.types import OID


class BaseSchema(pydantic.BaseModel):
    """Class using as a base class for schemas.py"""

    oid: typing.Optional[OID] = pydantic.Field(alias="oid")

    class Config(BaseConfiguration):
        """configuration class"""


class CreatedUpdatedBaseSchema(BaseSchema):
    """Append datetime fields for schema"""

    created_at: typing.Optional[datetime.datetime]
    updated_at: typing.Optional[datetime.datetime]

    class Config(BaseConfiguration):
        """configuration class"""
