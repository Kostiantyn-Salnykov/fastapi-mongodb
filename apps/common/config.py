from functools import lru_cache

from pydantic import BaseSettings

__all__ = ["common_settings"]


class CommonSettings(BaseSettings):
    PAGINATION_DEFAULT_LIMIT: int = 100
    PAGINATION_DEFAULT_OFFSET: int = 0
    PAGINATION_MAX_LIMIT: int = 1000
    PAGINATION_MIN_LIMIT: int = 1
    PAGINATION_MIN_OFFSET: int = 0


@lru_cache()
def get_settings() -> CommonSettings:
    return CommonSettings()


common_settings: CommonSettings = get_settings()
