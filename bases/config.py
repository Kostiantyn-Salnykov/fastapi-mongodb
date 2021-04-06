import datetime
import functools

import bson
import orjson
import pydantic

__all__ = ["bases_settings", "BaseConfiguration"]


class BasesSettings(pydantic.BaseSettings):
    PAGINATION_DEFAULT_LIMIT: int = 100
    PAGINATION_DEFAULT_OFFSET: int = 0
    PAGINATION_MAX_LIMIT: int = 1000
    PAGINATION_MIN_LIMIT: int = 1
    PAGINATION_MIN_OFFSET: int = 0


@functools.lru_cache()
def get_settings() -> BasesSettings:
    return BasesSettings()


bases_settings: BasesSettings = get_settings()


class BaseConfiguration(pydantic.BaseConfig):
    """base configuration class for Models and Schemas"""

    allow_population_by_field_name = True
    use_enum_values = True
    json_encoders = {  # pragma: no cover
        datetime.datetime: lambda dt: dt.timestamp(),
        bson.ObjectId: str,
    }
    json_dumps = orjson.dumps
    json_loads = orjson.loads
