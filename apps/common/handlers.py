from typing import List
import pymongo
from apps.common.exceptions import HandlerException


def mongo_duplicate_key_error_handler(model_name: str, fields: List[str], error: pymongo.errors.DuplicateKeyError):
    error_details = error.details.get("keyValue", {})
    for field in fields:
        if field in error_details:
            raise HandlerException(f"{model_name} with this '{error_details[field]}' {field} already exists")
    raise HandlerException("Unexpected duplication error")
