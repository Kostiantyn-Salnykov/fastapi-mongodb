import functools
import logging
import pathlib

import pydantic

__all__ = ["Settings"]

PROJECT_BASE_DIR = pathlib.Path(__file__).resolve().parent


class SettingsClass(pydantic.BaseSettings):
    PROJECT_NAME: str = pydantic.Field(default="Quick start FastAPI")
    BASE_DIR: pydantic.DirectoryPath = pydantic.Field(default=PROJECT_BASE_DIR)
    DEBUG: bool = pydantic.Field(default=False)
    RELOAD: bool = pydantic.Field(default=False)
    COLOR_LOGS: bool = pydantic.Field(default=False)
    LOGGER_NAME: str = pydantic.Field(default="MAIN_LOGGER")
    LOGGER_LEVEL: int = pydantic.Field(default=logging.INFO)
    HOST: str = pydantic.Field(default="0.0.0.0")
    PORT: int = pydantic.Field(default=9000)
    MONGO_URL: str = pydantic.Field(default="mongodb://0.0.0.0:27017")
    MONGO_DB_NAME: str = pydantic.Field(default="FastAPITemplate")
    ORIGINS_LIST: list[str] = pydantic.Field(default=["*"], env="ORIGINS")
    SECRET_KEY: str = pydantic.Field(default="SECRET")
    JWT_ACCESS_DELTA_MINUTES: int = pydantic.Field(default=1440)  # 30
    JWT_REFRESH_DELTA_MINUTES: int = pydantic.Field(default=1440)
    JWT_ISSUER: str = pydantic.Field(default="FastAPITemplate Back-end")
    JWT_ACCESS_AUDIENCE: str = pydantic.Field(default="ACCESS")
    JWT_REFRESH_AUDIENCE: str = pydantic.Field(default="REFRESH")
    MONGO_TEST_URL: str = pydantic.Field(default="mongodb://0.0.0.0:27017")
    MONGO_TEST_DB_NAME: str = pydantic.Field(default="test_db")
    MONGO_LOGGER_COMMAND: bool = pydantic.Field(default=False)
    MONGO_LOGGER_CONNECTION_POOL: bool = pydantic.Field(default=False)
    MONGO_LOGGER_HEARTBEAT: bool = pydantic.Field(default=False)
    MONGO_LOGGER_SERVER: bool = pydantic.Field(default=False)
    MONGO_LOGGER_TOPOLOGY: bool = pydantic.Field(default=False)

    class Config:
        env_file = PROJECT_BASE_DIR / ".env"


@functools.lru_cache()
def get_settings() -> SettingsClass:
    return SettingsClass()


Settings: SettingsClass = get_settings()
