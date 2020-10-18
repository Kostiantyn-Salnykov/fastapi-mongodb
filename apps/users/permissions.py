from fastapi import Request

from apps.common.permissions import IsAuthenticated
from apps.users.enums import UserRoles
from bases.exceptions import PermissionException


class IsAdmin(IsAuthenticated):
    def check(self, request: Request):
        super().check(request=request)

        if UserRoles.ADMIN not in request.auth.scopes:
            raise PermissionException(detail=f"This role is required: '{UserRoles.ADMIN}'")


class IsAdminOrSameClient(IsAuthenticated):
    def __init__(self, param_name: str = "_id", in_path: bool = True):
        self.param_name = param_name
        self.in_path = in_path

    def check(self, request: Request):
        super().check(request=request)

        try:
            IsAdmin().check(request=request)
            return
        except PermissionException:
            pass

        if self.in_path:
            query_user_id = request.path_params.get(self.param_name, None)
        else:
            query_user_id = request.query_params.get(self.param_name)

        if query_user_id and str(request.user.id) != query_user_id:
            raise PermissionException()
