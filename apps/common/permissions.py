from apps.common.bases import BasePermission
from fastapi import status, Request

from apps.common.exceptions import PermissionException


class IsAuthenticated(BasePermission):
    def check(self, request: Request):
        if not request.user:
            raise PermissionException(detail="Not authenticated", status_code=status.HTTP_401_UNAUTHORIZED)
