import pydantic
from functools import lru_cache


__all__ = ["users_settings"]


class UsersSettings(pydantic.BaseSettings):
    USERS_COL: str = pydantic.Field(default="users")


@lru_cache()
def get_settings() -> UsersSettings:
    return UsersSettings()


users_settings: UsersSettings = get_settings()
