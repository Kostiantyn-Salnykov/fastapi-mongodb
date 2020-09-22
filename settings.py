import pathlib
from functools import lru_cache

import pydantic

__all__ = ["settings"]

PROJECT_BASE_DIR = pathlib.Path(__file__).resolve().parent


class Settings(pydantic.BaseSettings):
    BASE_DIR: pydantic.DirectoryPath = pydantic.Field(default=PROJECT_BASE_DIR)
    DEBUG: bool = pydantic.Field(default=False)
    RELOAD: bool = pydantic.Field(default=False)
    COLOR_LOGS: bool = pydantic.Field(default=False)
    HOST: str = pydantic.Field(default="0.0.0.0")
    PORT: int = pydantic.Field(default=9000)
    MONGO_URL: str = pydantic.Field(default="mongodb://0.0.0.0:27017")
    MONGO_DB_NAME: str = pydantic.Field(default="FastAPITemplate")
    ORIGINS_LIST: list = pydantic.Field(default=["*"], env="ORIGINS")
    SECRET_KEY: str = pydantic.Field(default="SECRET")
    JWT_ACCESS_DELTA_MINUTES: int = pydantic.Field(default=1440)  # 30
    JWT_REFRESH_DELTA_MINUTES: int = pydantic.Field(default=1440)
    JWT_ISSUER: str = pydantic.Field(default="FastAPITemplate Back-end")
    JWT_ACCESS_AUDIENCE: str = pydantic.Field(default="ACCESS")
    JWT_REFRESH_AUDIENCE: str = pydantic.Field(default="REFRESH")

    class Config:
        env_file = PROJECT_BASE_DIR / ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
