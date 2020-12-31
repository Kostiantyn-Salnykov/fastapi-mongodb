"""Backends for JWT"""
from starlette.authentication import AuthenticationBackend, AuthenticationError, AuthCredentials
from starlette.requests import HTTPConnection

import bases
from apps.users.handlers import UsersHandler
from apps.users.models import UserModel
from apps.users.schemas import JWTPayloadSchema


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
            payload: JWTPayloadSchema = UsersHandler.decode_jwt(token=token, convert_to=JWTPayloadSchema)
            user_model: UserModel = await UsersHandler().retrieve_user(
                request=conn, query={"_id": payload.object_id, "is_active": True}
            )
        except bases.exceptions.HandlerException as error:
            raise AuthenticationError(str(error)) from error

        # request.auth, request.user
        return AuthCredentials(), user_model
