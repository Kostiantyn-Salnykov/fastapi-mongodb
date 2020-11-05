from typing import Optional

import pydantic

from bases.models import BaseMongoDBModel, BaseCreatedUpdatedModel


class UserModel(BaseMongoDBModel, BaseCreatedUpdatedModel):
    email: pydantic.EmailStr
    first_name: Optional[str] = pydantic.Field(default=None)
    last_name: Optional[str] = pydantic.Field(default=None)
    password_hash: Optional[str]
    is_active: Optional[bool] = pydantic.Field(default=True)

    class Config(BaseMongoDBModel.Config):
        sorting_default = "email"
        sorting_fields = ["email", "first_name", "last_name"]
