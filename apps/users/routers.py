import fastapi
from fastapi.security import HTTPBearer

import bases
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

users_router = fastapi.APIRouter()
login_router = fastapi.APIRouter()


@users_router.post(
    path="/users/",
    name="Create user",
    response_model=bases.schemas.InsertOneResultSchema,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def create_user(
    request: fastapi.Request, user: UserCreateSchema, users_handler: UsersHandler = fastapi.Depends(UsersHandler)
):
    return await users_handler.create_user(request=request, user=user)


@users_router.get(
    path="/users/{_id}/",
    name="Get user by '_id'",
    description="Retrieve user by '_id'",
    response_model=BaseUserSchema,
    dependencies=[fastapi.Depends(bearer_auth)],
)
async def get_user(
    request: fastapi.Request,
    _id: bases.types.OID = fastapi.Path(...),
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
):
    result = await users_handler.retrieve_user(request=request, query={"_id": _id})
    return result.dict()


@users_router.get(
    path="/whoami/",
    name="Get user from authorization",
    response_model=BaseUserSchema,
    dependencies=[fastapi.Depends(bearer_auth)],
)
async def whoami(
    request: fastapi.Request,
):
    return request.user.dict()


@users_router.get(
    path="/users/",
    response_model=list[BaseUserSchema],
    response_model_exclude_unset=True,
    dependencies=[fastapi.Depends(bearer_auth)],
)
async def get_users(
    request: fastapi.Request,
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
    paginator: bases.pagination.Paginator = fastapi.Depends(bases.pagination.LimitOffsetPagination()),
    projector: bases.projectors.BaseProjector = fastapi.Depends(bases.projectors.BaseProjector(model_class=UserModel)),
    sort_by: bases.sorting.SortBuilder = fastapi.Depends(bases.sorting.BaseSort()),
):
    return await users_handler.users_list(
        request=request, query={}, sort_by=sort_by, paginator=paginator, projector=projector
    )


@users_router.patch(
    path="/users/{_id}/",
    response_model=BaseUserSchema,
    dependencies=[fastapi.Depends(bearer_auth)],
)
async def update_user(
    request: fastapi.Request,
    _id: bases.types.OID = fastapi.Path(...),
    update: UserUpdateSchema = fastapi.Body(...),
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
):
    return await users_handler.update_user(request=request, _id=_id, update=update)


@users_router.delete(
    path="/users/{_id}/",
    response_model=bases.schemas.DeleteResultSchema,
    dependencies=[fastapi.Depends(bearer_auth)],
)
async def delete_user(
    request: fastapi.Request,
    _id: bases.types.OID = fastapi.Path(...),
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
):
    return await users_handler.delete_user(request=request, query={"_id": _id})


@login_router.post(
    path="/login/",
    response_model=JWTSchema,
)
async def login(
    request: fastapi.Request,
    credentials: UserLoginSchema,
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
):
    return await users_handler.login(request=request, credentials=credentials)


@login_router.post(path="/refresh/", response_model=JWTSchema)
async def refresh(
    data: JWTRefreshSchema = fastapi.Body(...),
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
):
    return await users_handler.refresh(data=data)
