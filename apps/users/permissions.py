import fastapi

from fastapi_mongodb.exceptions import PermissionException
from fastapi_mongodb.permissions import BasePermission


class IsAuthenticated(BasePermission):
    def __call__(self, request: fastapi.Request):
        if request.user is None:
            raise PermissionException()
