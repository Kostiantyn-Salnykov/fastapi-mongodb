import datetime
import typing

import bson
import pydantic

from fastapi_mongodb.schemas import BaseSchema, CreatedUpdatedBaseSchema
from fastapi_mongodb.types import OID

_ID = pydantic.Field(alias="_id")
FIRST_NAME = pydantic.Field(max_length=256, example="Jason")
LAST_NAME = pydantic.Field(max_length=256, example="Voorhees")
PASSWORD = pydantic.Field(min_length=8, max_length=1024, example="12345678")


class CodeSchema(BaseSchema):
    code: typing.Optional[str]


# TODO (Make fields.py to remove code duplication) kost:
class BaseUserSchema(BaseSchema, CreatedUpdatedBaseSchema):
    id: typing.Optional[OID] = _ID
    email: typing.Optional[pydantic.EmailStr]
    first_name: typing.Optional[str] = FIRST_NAME
    last_name: typing.Optional[str] = LAST_NAME
    is_active: typing.Optional[bool]
    codes: typing.Optional[list[CodeSchema]]


class UserCreateSchema(BaseSchema):
    """User create schema"""

    email: pydantic.EmailStr
    first_name: typing.Optional[str] = FIRST_NAME
    last_name: typing.Optional[str] = LAST_NAME
    password: str = PASSWORD


class UserUpdateSchema(UserCreateSchema):
    """User update schema"""

    email: typing.Optional[pydantic.EmailStr]
    password: typing.Optional[str] = PASSWORD


class UserLoginSchema(BaseSchema):
    """User login schema"""

    email: pydantic.EmailStr
    password: str = PASSWORD


class JWTSchema(BaseSchema):
    """JWT schema"""

    access: typing.Optional[str]
    refresh: typing.Optional[str]


class JWTRefreshSchema(BaseSchema):
    """JWT refresh schema"""

    refresh: pydantic.constr(max_length=4096)


class JWTPayloadSchema(BaseSchema):
    """JWT payload schema"""

    id: str = pydantic.Field()
    exp: datetime.datetime
    iat: datetime.datetime
    iss: str
    aud: str

    @property
    def object_id(self):
        return bson.ObjectId(self.id)
