"""Backends for JWT"""
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError
from starlette.requests import HTTPConnection

from apps.common.handlers import TokensHandler
from apps.users.handlers import UsersHandler
from apps.users.models import UserModel
from apps.users.schemas import JWTPayloadSchema
from bases.exceptions import HandlerException


class JWTTokenBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        if "Authorization" not in conn.headers:
            return AuthCredentials(), None

        auth_header = conn.headers["Authorization"]
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return AuthCredentials(), None
        except Exception as error:
            raise AuthenticationError("Invalid authentication credentials") from error

        try:
            payload: JWTPayloadSchema = TokensHandler.read_code(code=token, convert_to=JWTPayloadSchema)
            user_model: UserModel = await UsersHandler(request=conn).retrieve_user(
                request=conn, query={"_id": payload.object_id, "is_active": True}
            )
        except HandlerException as error:
            raise AuthenticationError(str(error)) from error

        # request.auth, request.user
        return AuthCredentials(), user_model
