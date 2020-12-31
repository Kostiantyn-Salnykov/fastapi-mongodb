import datetime
import typing

import bson
import pydantic

import bases


class AddressSchema(bases.schemas.BaseSchema):
    country: typing.Optional[str]
    city: typing.Optional[str]


# TODO (Make fields.py to remove code duplication) kost:
class BaseUserSchema(bases.schemas.BaseSchema, bases.schemas.CreatedUpdatedBaseSchema):
    id: typing.Optional[bases.types.OID] = pydantic.Field(alias="_id")
    email: typing.Optional[pydantic.EmailStr]
    first_name: typing.Optional[str] = pydantic.Field(max_length=256, example="Jason")
    last_name: typing.Optional[str] = pydantic.Field(max_length=256, example="Voorhees")
    is_active: typing.Optional[bool]
    address: typing.Optional[AddressSchema]


class UserCreateSchema(bases.schemas.BaseSchema):
    email: pydantic.EmailStr
    first_name: typing.Optional[str] = pydantic.Field(max_length=256, example="Jason")
    last_name: typing.Optional[str] = pydantic.Field(max_length=256, example="Voorhees")
    password: str = pydantic.Field(min_length=8, max_length=1024, example="12345678")


class UserUpdateSchema(UserCreateSchema):
    email: typing.Optional[pydantic.EmailStr]
    password: typing.Optional[str] = pydantic.Field(min_length=8, max_length=1024, example="12345678")
    is_active: typing.Optional[bool]
    address: typing.Optional[AddressSchema]


class UserLoginSchema(bases.schemas.BaseSchema):
    email: pydantic.EmailStr
    password: str = pydantic.Field(min_length=8, max_length=1024, example="12345678")


class JWTSchema(bases.schemas.BaseSchema):
    access: typing.Optional[str]
    refresh: typing.Optional[str]


class JWTRefreshSchema(bases.schemas.BaseSchema):
    refresh: pydantic.constr(max_length=4096)


class JWTPayloadSchema(bases.schemas.BaseSchema):
    id: str = pydantic.Field()
    exp: datetime.datetime
    iat: datetime.datetime
    iss: str
    aud: str

    @property
    def object_id(self):
        return bson.ObjectId(self.id)
