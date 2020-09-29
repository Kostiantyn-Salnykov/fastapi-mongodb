import datetime
from typing import Optional

import pydantic

from apps.common.bases import BaseSchema, OID


class CreatedUpdatedBaseSchema(pydantic.BaseModel):
    """Append datetime fields for schema"""

    created_datetime: Optional[datetime.datetime]
    updated_datetime: Optional[datetime.datetime]


class InsertOneResultSchema(BaseSchema):
    acknowledged: bool
    inserted_id: OID


class DeleteResultSchema(BaseSchema):
    acknowledged: bool
    deleted_count: int
