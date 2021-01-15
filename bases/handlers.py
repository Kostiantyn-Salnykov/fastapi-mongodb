import pymongo.errors

import bases


# TODO (Refactor this func to use in handlers or repositories) kost: 
def mongo_duplicate_key_error_handler(
    model_name: str, fields: list[str], error: pymongo.errors.DuplicateKeyError
):  # pragma: no cover
    error_details = error.details.get("keyValue", {})
    for field in fields:
        if field in error_details:
            raise bases.exceptions.HandlerException(
                f"{model_name} with this '{error_details[field]}' {field} already exists"
            )
    raise bases.exceptions.HandlerException("Unexpected duplication error")
