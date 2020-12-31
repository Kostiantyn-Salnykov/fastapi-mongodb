import pymongo.errors

import bases


def mongo_duplicate_key_error_handler(model_name: str, fields: list[str], error: pymongo.errors.DuplicateKeyError):
    error_details = error.details.get("keyValue", {})
    for field in fields:
        if field in error_details:
            raise bases.exceptions.HandlerException(
                f"{model_name} with this '{error_details[field]}' {field} already exists"
            )
    raise bases.exceptions.HandlerException("Unexpected duplication error")
