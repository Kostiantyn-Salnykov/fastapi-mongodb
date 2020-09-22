from typing import List

from fastapi import Request, APIRouter, Depends, Body, status, Path
from fastapi.security import HTTPBearer

from apps.common.bases import OID, PermissionsHandler, Paginator, BaseSort
from apps.common.paginations import LimitOffsetPagination
from apps.common.permissions import IsAuthenticated
from apps.common.schemas import InsertOneResultSchema, DeleteResultSchema
from apps.users.handlers import UsersHandler
from apps.users.permissions import IsAdminOrSameClient, IsAdmin
from apps.users.schemas import (
    UserCreateSchema,
    UserLoginSchema,
    JWTSchema,
    JWTRefreshSchema,
    BaseUserSchema,
    UserUpdateSchema,
)

__all__ = ["users_router", "login_router"]

bearer_auth = HTTPBearer(auto_error=False)

users_router = APIRouter()
login_router = APIRouter()


@users_router.post(
    path="/users/",
    name="Create user",
    response_model=InsertOneResultSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(request: Request, user: UserCreateSchema, users_handler: UsersHandler = Depends(UsersHandler)):
    return await users_handler.create_user(request=request, user=user)


@users_router.get(
    path="/users/{_id}/",
    name="Get user by '_id'",
    description="Retrieve user by '_id'",
    response_model=BaseUserSchema,
    dependencies=[Depends(bearer_auth), Depends(PermissionsHandler(permissions=[IsAdminOrSameClient()]))],
)
async def retrieve_user(request: Request, _id: OID = Path(...), users_handler: UsersHandler = Depends(UsersHandler)):
    result = await users_handler.retrieve_user(request=request, query={"_id": _id})
    return result.dict()


@users_router.get(
    path="/whoami/",
    name="Get user from authorization",
    response_model=BaseUserSchema,
    dependencies=[Depends(bearer_auth), Depends(PermissionsHandler(permissions=[IsAuthenticated()]))],
)
async def whoami(
    request: Request,
):
    return request.user.dict()


@users_router.get(
    path="/users/",
    response_model=List[BaseUserSchema],
    dependencies=[Depends(bearer_auth), Depends(PermissionsHandler(permissions=[IsAdmin()]))],
)
async def users_list(
    request: Request,
    users_handler: UsersHandler = Depends(UsersHandler),
    paginator: Paginator = Depends(LimitOffsetPagination()),
    sort_by: BaseSort = Depends(BaseSort),
):
    result = await users_handler.users_list(request=request, query={}, sort_by=sort_by, paginator=paginator)
    return result


@users_router.patch(
    path="/users/{_id}/",
    response_model=BaseUserSchema,
    dependencies=[Depends(bearer_auth), Depends(PermissionsHandler(permissions=[IsAdminOrSameClient()]))],
)
async def update_user(
    request: Request,
    _id: OID = Path(...),
    update: UserUpdateSchema = Body(...),
    users_handler: UsersHandler = Depends(UsersHandler),
):
    return await users_handler.update_user(request=request, _id=_id, update=update)


@users_router.delete(
    path="/users/{_id}/",
    response_model=DeleteResultSchema,
    dependencies=[Depends(bearer_auth), Depends(PermissionsHandler(permissions=[IsAdmin()]))],
)
async def delete_user(request: Request, _id: OID = Path(...), users_handler: UsersHandler = Depends(UsersHandler)):
    return await users_handler.delete_user(request=request, query={"_id": _id})


@login_router.post(
    path="/login/",
    response_model=JWTSchema,
)
async def login(
    request: Request,
    credentials: UserLoginSchema,
    users_handler: UsersHandler = Depends(UsersHandler),
):
    return await users_handler.login(request=request, credentials=credentials)


@login_router.post(path="/refresh/", response_model=JWTSchema)
async def refresh(
    data: JWTRefreshSchema = Body(...),
    users_handler: UsersHandler = Depends(UsersHandler),
):
    return await users_handler.refresh(data=data)
