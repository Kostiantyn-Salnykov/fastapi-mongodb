import fastapi
import fastapi.middleware.cors
from starlette.middleware.authentication import AuthenticationMiddleware

import bases
import settings
from apps.common.middlewares import MongoSessionMiddleware, ExceptionsMiddleware
from apps.users.backends import JWTTokenBackend
from apps.users.routers import users_router, login_router

__all__ = ["App"]

App = fastapi.FastAPI(
    version="0.0.1",
    debug=settings.Settings.DEBUG,
    title=settings.Settings.PROJECT_NAME,
    description="Quick start FastAPI project template",
    default_response_class=fastapi.responses.ORJSONResponse,
)


@App.on_event("startup")
async def setup_db():
    """Create mongodb connection and indexes"""
    bases.db.MongoDBHandler.create_client()


@App.on_event("shutdown")
async def close_db():
    """Close mongodb connection"""
    bases.db.MongoDBHandler.delete_client()


App.add_middleware(middleware_class=ExceptionsMiddleware)

App.add_middleware(
    middleware_class=AuthenticationMiddleware,
    backend=JWTTokenBackend(),
    on_error=lambda conn, exc: fastapi.responses.ORJSONResponse(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)}
    ),
)

App.add_middleware(middleware_class=MongoSessionMiddleware)

App.add_middleware(
    middleware_class=fastapi.middleware.cors.CORSMiddleware,
    allow_origins=settings.Settings.ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

App.include_router(router=users_router, tags=["users"])

App.include_router(router=login_router, tags=["authentication"])
