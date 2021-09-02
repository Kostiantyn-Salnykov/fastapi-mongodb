import bson


class OID(str):
    """ObjectId type for BaseMongoDBModels and BaseSchemas"""

    @classmethod
    def __modify_schema__(cls, field_schema):
        """Update OpenAPI docs schema"""
        field_schema.update(
            pattern="^[a-f0-9]{24}$",
            example="5f5cf6f50cde9ec07786b294",
            title="ObjectId",
            type="string",
        )

    @classmethod
    def __get_validators__(cls):
        """Default method for Pydantic Types"""
        yield cls.validate

    @classmethod
    def validate(cls, v) -> bson.ObjectId:
        """Default validation for Pydantic Types"""
        try:
            value = bson.ObjectId(oid=str(v))
        except bson.errors.InvalidId as error:
            raise ValueError(error) from error
        else:
            return value
