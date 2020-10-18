import datetime
from typing import Optional, List

import bson
import pydantic

import bases.types
from apps.users.enums import UserRoles
from bases.schemas import CreatedUpdatedBaseSchema, BaseSchema


# TODO: Make fields.py to remove code duplication
class BaseUserSchema(BaseSchema, CreatedUpdatedBaseSchema):
    id: Optional[bases.types.OID] = pydantic.Field(alias="_id")
    email: Optional[pydantic.EmailStr]
    first_name: Optional[str] = pydantic.Field(max_length=256, example="Jason")
    last_name: Optional[str] = pydantic.Field(max_length=256, example="Voorhees")
    is_active: Optional[bool]
    roles: Optional[List[UserRoles]]


class UserCreateSchema(BaseSchema):
    email: pydantic.EmailStr
    first_name: Optional[str] = pydantic.Field(max_length=256, example="Jason")
    last_name: Optional[str] = pydantic.Field(max_length=256, example="Voorhees")
    password: str = pydantic.Field(min_length=8, max_length=1024, example="12345678")


class UserUpdateSchema(UserCreateSchema):
    email: Optional[pydantic.EmailStr]
    password: Optional[str] = pydantic.Field(min_length=8, max_length=1024, example="12345678")
    is_active: Optional[bool]
    roles: Optional[List[UserRoles]]


class UserLoginSchema(BaseSchema):
    email: pydantic.EmailStr
    password: str = pydantic.Field(min_length=8, max_length=1024, example="12345678")


class JWTSchema(BaseSchema):
    access: Optional[str]
    refresh: Optional[str]


class JWTRefreshSchema(BaseSchema):
    refresh: pydantic.constr(max_length=4096)


class JWTPayloadSchema(BaseSchema):
    id: str = pydantic.Field()
    exp: datetime.datetime
    iat: datetime.datetime
    iss: str
    aud: str

    @property
    def object_id(self):
        return bson.ObjectId(self.id)
