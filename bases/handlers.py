import fastapi
import pymongo.errors

import bases.permissions
from bases.exceptions import HandlerException


def mongo_duplicate_key_error_handler(model_name: str, fields: list[str], error: pymongo.errors.DuplicateKeyError):
    error_details = error.details.get("keyValue", {})
    for field in fields:
        if field in error_details:
            raise HandlerException(f"{model_name} with this '{error_details[field]}' {field} already exists")
    raise HandlerException("Unexpected duplication error")


class PermissionsHandler:
    """Class to check list of permissions inside FastAPI Depends"""

    def __init__(self, permissions: list[bases.permissions.BasePermission]):
        self.permissions = permissions

    async def __call__(self, request: fastapi.Request):
        """Class becomes callable that allow to use it inside FastAPI Depends"""
        for permission in self.permissions:
            try:
                permission.check(request=request)
            except bases.exceptions.PermissionException as exception:
                raise fastapi.HTTPException(status_code=exception.status_code, detail=exception.detail) from exception
