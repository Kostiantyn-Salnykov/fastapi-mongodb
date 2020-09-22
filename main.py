from fastapi import FastAPI, responses, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from apps.common.db import create_mongo_connection, close_mongo_connection
from apps.common.middlewares import MongoSessionMiddleware, ExceptionsMiddleware
from apps.users.backends import JWTTokenBackend
from apps.users.routers import users_router, login_router
from settings import settings

__all__ = ["app"]

app = FastAPI(
    version="0.0.1",
    debug=settings.DEBUG,
    title="Quick start FastAPI",
    description="Quick start FastAPI project template",
    default_response_class=responses.ORJSONResponse,
)


@app.on_event("startup")
async def setup_db():
    """Create mongodb connection and indexes"""
    create_mongo_connection()


@app.on_event("shutdown")
async def close_db():
    """Close mongodb connection"""
    close_mongo_connection()


app.add_middleware(middleware_class=ExceptionsMiddleware)

app.add_middleware(
    middleware_class=AuthenticationMiddleware,
    backend=JWTTokenBackend(),
    on_error=lambda conn, exc: responses.ORJSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)}
    ),
)

app.add_middleware(middleware_class=MongoSessionMiddleware)

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=settings.ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=users_router, tags=["users"])

app.include_router(router=login_router, tags=["authentication"])
