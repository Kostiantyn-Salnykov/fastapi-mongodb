import functools

import pydantic

__all__ = ["users_settings"]


class UsersSettings(pydantic.BaseSettings):
    USERS_COL: str = pydantic.Field(default="users")


@functools.lru_cache()
def get_settings() -> UsersSettings:
    return UsersSettings()


users_settings: UsersSettings = get_settings()
