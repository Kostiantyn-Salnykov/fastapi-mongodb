import fastapi

import bases


class IsAuthenticated(bases.permissions.BasePermission):
    def __call__(self, request: fastapi.Request):
        if request.user is None:
            raise bases.exceptions.PermissionException()
