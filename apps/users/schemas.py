import datetime
from typing import Optional, List

import bson
import pydantic

from apps.common.bases import BaseSchema, OID, CreatedUpdatedBaseSchema
from apps.users.enums import UserRoles


class BaseUserSchema(BaseSchema, CreatedUpdatedBaseSchema):
    id: OID
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
    password_confirm: str = pydantic.Field(min_length=8, max_length=1024, example="12345678")

    @pydantic.validator("password_confirm", always=True)
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("'password' and 'password_confirm' do not match")
        return v


class UserUpdateSchema(UserCreateSchema):
    email: Optional[pydantic.EmailStr]
    password: Optional[str] = pydantic.Field(min_length=8, max_length=1024, example="12345678")
    password_confirm: Optional[str] = pydantic.Field(min_length=8, max_length=1024, example="12345678")
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
