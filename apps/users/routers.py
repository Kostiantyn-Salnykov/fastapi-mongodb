from fastapi import Request, APIRouter, Depends, Body, status, Path
from fastapi.security import HTTPBearer

import bases.pagination
import bases.projectors
import bases.schemas
import bases.sorting
import bases.types
from apps.users.handlers import UsersHandler
from apps.users.models import UserModel
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
    response_model=bases.schemas.InsertOneResultSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(request: Request, user: UserCreateSchema, users_handler: UsersHandler = Depends(UsersHandler)):
    return await users_handler.create_user(request=request, user=user)


@users_router.get(
    path="/users/{_id}/",
    name="Get user by '_id'",
    description="Retrieve user by '_id'",
    response_model=BaseUserSchema,
    dependencies=[Depends(bearer_auth)],
)
async def retrieve_user(
    request: Request, _id: bases.types.OID = Path(...), users_handler: UsersHandler = Depends(UsersHandler)
):
    result = await users_handler.retrieve_user(request=request, query={"_id": _id})
    return result.dict()


@users_router.get(
    path="/whoami/",
    name="Get user from authorization",
    response_model=BaseUserSchema,
    dependencies=[Depends(bearer_auth)],
)
async def whoami(
    request: Request,
):
    return request.user.dict()


@users_router.get(
    path="/users/",
    response_model=list[BaseUserSchema],
    response_model_exclude_unset=True,
    dependencies=[Depends(bearer_auth)],
)
async def users_list(
    request: Request,
    users_handler: UsersHandler = Depends(UsersHandler),
    paginator: bases.pagination.Paginator = Depends(bases.pagination.LimitOffsetPagination()),
    projector: bases.projectors.BaseProjector = Depends(bases.projectors.BaseProjector(model_class=UserModel)),
    sort_by: bases.sorting.BaseSort = Depends(bases.sorting.BaseSort(model=UserModel)),
):
    result = await users_handler.users_list(
        request=request, query={}, sort_by=sort_by, paginator=paginator, projector=projector
    )
    return result


@users_router.patch(
    path="/users/{_id}/",
    response_model=BaseUserSchema,
    dependencies=[Depends(bearer_auth)],
)
async def update_user(
    request: Request,
    _id: bases.types.OID = Path(...),
    update: UserUpdateSchema = Body(...),
    users_handler: UsersHandler = Depends(UsersHandler),
):
    return await users_handler.update_user(request=request, _id=_id, update=update)


@users_router.delete(
    path="/users/{_id}/",
    response_model=bases.schemas.DeleteResultSchema,
    dependencies=[Depends(bearer_auth)],
)
async def delete_user(
    request: Request, _id: bases.types.OID = Path(...), users_handler: UsersHandler = Depends(UsersHandler)
):
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
