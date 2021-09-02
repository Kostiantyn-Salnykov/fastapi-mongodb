import datetime

import bson
import orjson
import pydantic
import pydantic.json


__all__ = ["BaseConfiguration"]


class BaseConfiguration(pydantic.BaseConfig):
    """base configuration class for Models and Schemas"""

    allow_population_by_field_name = True
    use_enum_values = True
    json_encoders = {  # pragma: no cover
        datetime.datetime: lambda date_time: pydantic.json.isoformat(date_time),
        datetime.timedelta: lambda time_delta: pydantic.json.timedelta_isoformat(time_delta),
        bson.ObjectId: str,
    }
    json_dumps = orjson.dumps
    json_loads = orjson.loads
