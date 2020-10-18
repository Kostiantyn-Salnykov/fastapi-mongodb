import binascii
import datetime
import hashlib
import secrets
from typing import List

import jwt
import pymongo
from fastapi import Request
from pymongo.results import InsertOneResult

import bases.repositories
import bases.sorting
import bases.types
import bases.projectors
import bases.pagination
from apps.users.models import UserModel
from apps.users.permissions import IsAdmin
from apps.users.repositories import UserRepository
from apps.users.schemas import UserCreateSchema, UserLoginSchema, JWTRefreshSchema, JWTPayloadSchema, UserUpdateSchema
from bases.exceptions import HandlerException, PermissionException, RepositoryException
from settings import settings

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
                minutes=settings.JWT_REFRESH_DELTA_MINUTES if refresh else settings.JWT_ACCESS_DELTA_MINUTES
            ),
            "iat": creation_datetime,
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_REFRESH_AUDIENCE if refresh else settings.JWT_ACCESS_AUDIENCE,
        }
        return (jwt.encode(payload=payload, key=settings.SECRET_KEY)).decode("UTF-8")

    @staticmethod
    def decode_jwt(token, refresh: bool = False, convert_to=None):
        try:
            payload = jwt.decode(
                jwt=token,
                key=settings.SECRET_KEY,
                algorithms=["HS256"],
                issuer=settings.JWT_ISSUER,
                audience=settings.JWT_REFRESH_AUDIENCE if refresh else settings.JWT_ACCESS_AUDIENCE,
            )
            if convert_to is not None:
                payload = convert_to(**payload)
        except jwt.ExpiredSignatureError:
            raise HandlerException("Token signature expired")
        except jwt.InvalidIssuerError:
            raise HandlerException("Invalid token issuer")
        except jwt.InvalidAudienceError:
            raise HandlerException("Invalid token audience")
        except jwt.InvalidSignatureError:
            raise HandlerException("Invalid token signature")
        # base exceptions
        except jwt.DecodeError:
            raise HandlerException("Can't decode token")
        except jwt.InvalidTokenError:
            raise HandlerException("Invalid token")
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

    async def create_user(self, request: Request, user: UserCreateSchema) -> dict:
        """Create new user"""
        user_model = UserModel(
            password_hash=self.make_password(password=user.password), **user.dict(exclude_unset=True)
        )
        result: InsertOneResult = await self.user_repository.insert_one(
            document=user_model.to_db(),
            session=request.state.mongo_session,
        )
        return {"acknowledged": result.acknowledged, "inserted_id": result.inserted_id}

    async def retrieve_user(self, request: Request, query: dict):
        result: UserModel = await self.user_repository.find_one(query=query, session=request.state.mongo_session)
        return result

    async def users_list(
        self,
        request: Request,
        query: dict,
        sort_by: bases.sorting.BaseSort,
        paginator: bases.pagination.Paginator,
        projector: bases.projectors.BaseProjector,
    ):
        result: List[UserModel] = await self.user_repository.find(
            query=query,
            sort=sort_by.to_db(),
            skip=paginator.skip,
            limit=paginator.limit,
            session=request.state.mongo_session,
            projection=projector.to_db(),
            repository_config=bases.repositories.BaseRepositoryConfig(convert=False),
        )
        return result

    async def delete_user(self, request: Request, query: dict):
        result = await self.user_repository.delete_one(query=query, session=request.state.mongo_session)
        return {"acknowledged": result.acknowledged, "deleted_count": result.deleted_count}

    async def update_user(self, request: Request, _id: bases.types.OID, update: UserUpdateSchema):
        try:
            IsAdmin().check(request=request)
            exclude_set = set()
        except PermissionException:
            exclude_set = UserModel.Config.update_by_admin_only
        update_dict = update.dict(exclude_unset=True, exclude=exclude_set)
        if update_dict:
            password = update_dict.pop("password", None)
            if password is not None:
                update_dict["password_hash"] = self.make_password(password=password)
            update_dict["updated_datetime"] = datetime.datetime.utcnow()
            user: UserModel = await self.user_repository.find_one_and_update(
                query={"_id": _id},
                update={"$set": update_dict},
                session=request.state.mongo_session,
                return_document=pymongo.ReturnDocument.AFTER,
            )
        else:
            user: UserModel = await self.user_repository.find_one(
                query={"_id": _id}, session=request.state.mongo_session
            )
        return user.dict()

    async def login(self, request: Request, credentials: UserLoginSchema) -> dict:
        try:
            user: UserModel = await self.retrieve_user(
                request=request, query={"email": credentials.email, "is_active": True}
            )
        except RepositoryException:
            pass
        else:
            if self.check_password(password=credentials.password, password_hash=user.password_hash):
                return {
                    "access": self.encode_jwt(_id=str(user.id)),
                    "refresh": self.encode_jwt(_id=str(user.id), refresh=True),
                }
        raise HandlerException("Invalid credentials.")

    async def refresh(self, data: JWTRefreshSchema) -> dict:
        payload: JWTPayloadSchema = self.decode_jwt(token=data.refresh, refresh=True, convert_to=JWTPayloadSchema)
        return {"access": self.encode_jwt(_id=payload.id), "refresh": self.encode_jwt(_id=payload.id, refresh=True)}
