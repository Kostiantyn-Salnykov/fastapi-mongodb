import fastapi

import bases.exceptions
import bases.permissions


class IsAuthenticated(bases.permissions.BasePermission):
    def check(self, request: fastapi.Request):
        if not request.user:
            raise bases.exceptions.PermissionException(
                detail="Not authenticated", status_code=fastapi.status.HTTP_401_UNAUTHORIZED
            )
