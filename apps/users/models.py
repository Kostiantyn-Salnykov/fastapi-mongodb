import typing

import pydantic
import pymongo

import bases


class Address(bases.models.BaseMongoDBModel):
    country: str
    city: str


class UserModel(bases.models.BaseCreatedUpdatedModel, bases.models.BaseMongoDBModel):
    email: pydantic.EmailStr
    first_name: typing.Optional[str] = pydantic.Field(default=None)
    last_name: typing.Optional[str] = pydantic.Field(default=None)
    password_hash: typing.Optional[str]
    is_active: typing.Optional[bool] = pydantic.Field(default=True)
    address: typing.Optional[Address]

    class Config(bases.models.BaseMongoDBModel.Config):
        sorting_default = [("email", pymongo.ASCENDING)]
        sorting_fields = ["_id", "email", "first_name", "last_name"]
