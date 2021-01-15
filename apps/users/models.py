import typing

import pydantic
import pymongo

import bases
from apps.common.enums import CodeAudiences


class UserCode(bases.models.BaseDBModel):
    code: str
    audience: CodeAudiences


class UserModel(bases.models.BaseCreatedUpdatedModel, bases.models.BaseDBModel):
    email: pydantic.EmailStr
    first_name: typing.Optional[str] = pydantic.Field(default=None)
    last_name: typing.Optional[str] = pydantic.Field(default=None)
    password_hash: typing.Optional[str]
    is_active: typing.Optional[bool] = pydantic.Field(default=True)
    codes: typing.Optional[list[UserCode]] = pydantic.Field(default_factory=list)

    class Config(bases.models.BaseDBModel.Config):
        sorting_default = [("email", pymongo.ASCENDING)]
        sorting_fields = ["_id", "email", "first_name", "last_name"]
