import fastapi
from fastapi.security import HTTPBearer

from apps.users.handlers import UsersHandler
from apps.users.models import UserModel
from apps.users.permissions import IsAuthenticated
from apps.users.schemas import (
    BaseUserSchema,
    JWTRefreshSchema,
    JWTSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserUpdateSchema,
)
from bases.pagination import LimitOffsetPagination, Paginator
from bases.projectors import BaseProjector
from bases.schemas import DeleteResultSchema, InsertOneResultSchema
from bases.sorting import BaseSort, SortBuilder
from bases.types import OID

__all__ = ["users_router", "login_router"]

bearer_auth = HTTPBearer(auto_error=False)

users_router = fastapi.APIRouter(prefix="/users", tags=["users"])
login_router = fastapi.APIRouter(tags=["authentication"])


@users_router.post(
    path="/",
    name="Create user",
    response_model=InsertOneResultSchema,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def create_user(
    request: fastapi.Request,
    user: UserCreateSchema,
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
):
    return await users_handler.create_user(request=request, user=user)


@users_router.get(
    path="/whoami/",
    name="Get user from authorization",
    response_model=BaseUserSchema,
    dependencies=[fastapi.Depends(bearer_auth), fastapi.Depends(IsAuthenticated())],
)
async def whoami(
    request: fastapi.Request,
):
    return request.user.dict()


@users_router.get(
    path="/{_id}/",
    name="Get user by '_id'",
    description="Retrieve user by '_id'",
    response_model=BaseUserSchema,
    dependencies=[fastapi.Depends(bearer_auth), fastapi.Depends(IsAuthenticated())],
)
async def get_user(
    request: fastapi.Request,
    _id: OID = fastapi.Path(...),
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
):
    result = await users_handler.retrieve_user(request=request, query={"_id": _id})
    return result.dict()


@users_router.get(
    path="/",
    response_model=list[BaseUserSchema],
    response_model_exclude_unset=True,
    dependencies=[fastapi.Depends(bearer_auth), fastapi.Depends(IsAuthenticated())],
)
async def get_users(
    request: fastapi.Request,
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
    paginator: Paginator = fastapi.Depends(LimitOffsetPagination()),
    projector: BaseProjector = fastapi.Depends(BaseProjector(model_class=UserModel)),
    sort_by: SortBuilder = fastapi.Depends(BaseSort()),
):
    return await users_handler.users_list(
        request=request,
        query={},
        sort_by=sort_by,
        paginator=paginator,
        projector=projector,
    )


@users_router.patch(
    path="/{_id}/",
    response_model=BaseUserSchema,
    dependencies=[fastapi.Depends(bearer_auth), fastapi.Depends(IsAuthenticated())],
)
async def update_user(
    request: fastapi.Request,
    _id: OID = fastapi.Path(...),
    update: UserUpdateSchema = fastapi.Body(...),
    users_handler: UsersHandler = fastapi.Depends(UsersHandler),
):
    return await users_handler.update_user(request=request, _id=_id, update=update)


@users_router.delete(
    path="/{_id}/",
    response_model=DeleteResultSchema,
    dependencies=[fastapi.Depends(bearer_auth), fastapi.Depends(IsAuthenticated())],
)
async def delete_user(
    request: fastapi.Request,
    _id: OID = fastapi.Path(...),
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
