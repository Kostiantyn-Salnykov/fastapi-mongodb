import functools

import pydantic

__all__ = ["common_settings"]


class CommonSettings(pydantic.BaseSettings):
    PAGINATION_DEFAULT_LIMIT: int = 100
    PAGINATION_DEFAULT_OFFSET: int = 0
    PAGINATION_MAX_LIMIT: int = 1000
    PAGINATION_MIN_LIMIT: int = 1
    PAGINATION_MIN_OFFSET: int = 0


@functools.lru_cache()
def get_settings() -> CommonSettings:
    return CommonSettings()


common_settings: CommonSettings = get_settings()
