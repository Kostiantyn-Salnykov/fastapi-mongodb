"""Customized configuration from pydantic to work with models and schemas."""
import datetime

import bson
import pydantic
import pydantic.json

try:
    import orjson

    json_dumps = orjson.dumps
    json_loads = orjson.loads
except ImportError:
    import json

    json_dumps = json.dumps
    json_loads = json.loads

__all__ = ["BaseConfiguration"]


class BaseConfiguration(pydantic.BaseConfig):
    """base configuration class for Models and Schemas."""

    allow_population_by_field_name = True
    use_enum_values = True
    json_encoders = {  # pragma: no cover
        datetime.datetime: lambda date_time: pydantic.json.isoformat(date_time),
        datetime.timedelta: lambda time_delta: pydantic.json.timedelta_isoformat(time_delta),
        bson.ObjectId: str,
    }
    json_dumps = json_dumps
    json_loads = json_loads
