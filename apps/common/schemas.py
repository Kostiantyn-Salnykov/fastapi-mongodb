from apps.common.bases import BaseSchema, OID


class InsertOneResultSchema(BaseSchema):
    acknowledged: bool
    inserted_id: OID


class DeleteResultSchema(BaseSchema):
    acknowledged: bool
    deleted_count: int
