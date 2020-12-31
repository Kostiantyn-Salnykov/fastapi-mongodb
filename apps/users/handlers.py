import binascii
import datetime
import hashlib
import secrets

import fastapi
import jwt
import pymongo
import pymongo.errors
import pymongo.results

import bases
import settings
from apps.users.models import UserModel
from apps.users.repositories import UserRepository
from apps.users.schemas import (
    UserCreateSchema,
    UserLoginSchema,
    JWTRefreshSchema,
    JWTPayloadSchema,
    UserUpdateSchema,
)

__all__ = ["UsersHandler"]


class UsersHandler:
    def __init__(self):
        self.user_repository = UserRepository()

    @staticmethod
    def encode_jwt(_id: str, refresh: bool = False):
        creation_datetime = datetime.datetime.utcnow()
        payload = {
            "id": _id,
            "exp": creation_datetime
            + datetime.timedelta(
                minutes=settings.Settings.JWT_REFRESH_DELTA_MINUTES
                if refresh
                else settings.Settings.JWT_ACCESS_DELTA_MINUTES
            ),
            "iat": creation_datetime,
            "iss": settings.Settings.JWT_ISSUER,
            "aud": settings.Settings.JWT_REFRESH_AUDIENCE if refresh else settings.Settings.JWT_ACCESS_AUDIENCE,
        }
        return jwt.encode(payload=payload, key=settings.Settings.SECRET_KEY)

    @staticmethod
    def decode_jwt(token, refresh: bool = False, convert_to=None):
        try:
            payload = jwt.decode(
                jwt=token,
                key=settings.Settings.SECRET_KEY,
                algorithms=["HS256"],
                issuer=settings.Settings.JWT_ISSUER,
                audience=settings.Settings.JWT_REFRESH_AUDIENCE if refresh else settings.Settings.JWT_ACCESS_AUDIENCE,
            )
            if convert_to is not None:
                payload = convert_to(**payload)
        except jwt.ExpiredSignatureError:
            raise bases.exceptions.HandlerException("Token signature expired")
        except jwt.InvalidIssuerError:
            raise bases.exceptions.HandlerException("Invalid token issuer")
        except jwt.InvalidAudienceError:
            raise bases.exceptions.HandlerException("Invalid token audience")
        except jwt.InvalidSignatureError:
            raise bases.exceptions.HandlerException("Invalid token signature")
        # base exceptions
        except jwt.DecodeError:
            raise bases.exceptions.HandlerException("Can't decode token")
        except jwt.InvalidTokenError:
            raise bases.exceptions.HandlerException("Invalid token")
        else:
            return payload

    @staticmethod
    def __hash(salt: str, password: str, encoding: str = "UTF-8") -> str:
        password_hash = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode(encoding=encoding),
            salt=salt.encode(encoding=encoding),
            iterations=100000,
        )
        password_hash = binascii.hexlify(password_hash).decode("utf-8")
        return password_hash

    def check_password(self, password: str, password_hash: str) -> bool:
        """Check password and hash"""
        salt = password_hash[:64]
        stored_password = password_hash[64:]
        check_password_hash = self.__hash(salt=salt, password=password)
        return check_password_hash == stored_password

    def make_password(self, password: str) -> str:
        """Make hash from password"""
        salt = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        new_password_hash = self.__hash(salt=salt, password=password)
        return salt + new_password_hash

    async def create_user(self, request: fastapi.Request, user: UserCreateSchema) -> dict:
        """Create new user"""
        user_model = UserModel(
            password_hash=self.make_password(password=user.password), **user.dict(exclude_unset=True)
        )
        try:
            result: pymongo.results.InsertOneResult = await self.user_repository.insert_one(
                document=user_model.to_db(),
                session=request.state.mongo_session,
            )
        except pymongo.errors.DuplicateKeyError as error:
            bases.handlers.mongo_duplicate_key_error_handler(model_name="User", fields=["email"], error=error)
        else:
            return {"acknowledged": result.acknowledged, "inserted_id": result.inserted_id}

    async def retrieve_user(self, request: fastapi.Request, query: dict):
        return await self.user_repository.find_one(query=query, session=request.state.mongo_session)

    async def users_list(
        self,
        request: fastapi.Request,
        query: dict,
        sort_by: bases.sorting.SortBuilder,
        paginator: bases.pagination.Paginator,
        projector: bases.projectors.BaseProjector,
    ):
        return await self.user_repository.find(
            query=query,
            sort=sort_by.to_db(model=UserModel),
            skip=paginator.skip,
            limit=paginator.limit,
            session=request.state.mongo_session,
            projection=projector.to_db(),
            repository_config=bases.repositories.BaseRepositoryConfig(convert=False),
        )

    async def delete_user(self, request: fastapi.Request, query: dict):
        result = await self.user_repository.delete_one(query=query, session=request.state.mongo_session)
        return {"acknowledged": result.acknowledged, "deleted_count": result.deleted_count}

    async def update_user(self, request: fastapi.Request, _id: bases.types.OID, update: UserUpdateSchema):
        update_dict = update.dict(exclude_unset=True)
        if update_dict:
            password = update_dict.pop("password", None)
            if password is not None:
                update_dict["password_hash"] = self.make_password(password=password)
            update_dict["updated_datetime"] = datetime.datetime.utcnow()
            user = await self.user_repository.find_one_and_update(
                query={"_id": _id},
                update={"$set": update_dict},
                session=request.state.mongo_session,
                return_document=pymongo.ReturnDocument.AFTER,
                repository_config=bases.repositories.BaseRepositoryConfig(convert=False)
            )
        else:
            user = await self.user_repository.find_one(
                query={"_id": _id}, session=request.state.mongo_session,
                repository_config=bases.repositories.BaseRepositoryConfig(convert=False)
            )
        user = UserModel.from_db(data=user)
        return user

    async def login(self, request: fastapi.Request, credentials: UserLoginSchema) -> dict:
        try:
            user: UserModel = await self.retrieve_user(
                request=request, query={"email": credentials.email, "is_active": True}
            )
        except bases.exceptions.RepositoryException:
            pass
        else:
            if self.check_password(password=credentials.password, password_hash=user.password_hash):
                return {
                    "access": self.encode_jwt(_id=str(user.id)),
                    "refresh": self.encode_jwt(_id=str(user.id), refresh=True),
                }
        raise bases.exceptions.HandlerException("Invalid credentials.")

    async def refresh(self, data: JWTRefreshSchema) -> dict:
        payload: JWTPayloadSchema = self.decode_jwt(token=data.refresh, refresh=True, convert_to=JWTPayloadSchema)
        return {"access": self.encode_jwt(_id=payload.id), "refresh": self.encode_jwt(_id=payload.id, refresh=True)}
