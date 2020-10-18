from typing import Optional, List

import pydantic

from apps.users.enums import UserRoles
from bases.models import BaseMongoDBModel


class UserModel(BaseMongoDBModel):
    email: pydantic.EmailStr
    first_name: Optional[str] = pydantic.Field(default=None)
    last_name: Optional[str] = pydantic.Field(default=None)
    password_hash: Optional[str]
    is_active: Optional[bool] = pydantic.Field(default=True)
    roles: List[UserRoles] = pydantic.Field(default=[UserRoles.CLIENT])

    class Config(BaseMongoDBModel.Config):
        use_datetime_fields = True
        update_by_admin_only: set = {"roles", "is_active"}
        sorting_default = "email"
        sorting_fields = ["email", "first_name", "last_name"]
