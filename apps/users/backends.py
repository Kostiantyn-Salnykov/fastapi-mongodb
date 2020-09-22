from starlette.authentication import AuthenticationBackend, AuthenticationError, AuthCredentials
from starlette.requests import HTTPConnection

from apps.common.exceptions import HandlerException
from apps.users.handlers import UsersHandler
from apps.users.models import UserModel
from apps.users.schemas import JWTPayloadSchema


class JWTTokenBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection, **kwargs):
        if "Authorization" not in conn.headers:
            return

        auth_header = conn.headers["Authorization"]
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return
        except Exception:
            raise AuthenticationError("Invalid authentication credentials")

        try:
            payload: JWTPayloadSchema = UsersHandler.decode_jwt(token=token, convert_to=JWTPayloadSchema)
            user_model: UserModel = await UsersHandler().retrieve_user(request=conn, query={"_id": payload.object_id})
        except HandlerException as error:
            raise AuthenticationError(str(error))

        # request.auth, request.user
        return AuthCredentials(scopes=user_model.roles), user_model
