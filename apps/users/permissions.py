import fastapi

from bases.exceptions import PermissionException
from bases.permissions import BasePermission


class IsAuthenticated(BasePermission):
    def __call__(self, request: fastapi.Request):
        if request.user is None:
            raise PermissionException()
