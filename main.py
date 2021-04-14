import fastapi
import fastapi.middleware.cors
from starlette.middleware.authentication import AuthenticationMiddleware

import settings
from apps.common.middlewares import DBSessionMiddleware, ExceptionsMiddleware
from apps.users.backends import JWTTokenBackend
from apps.users.handlers import UsersHandler
from apps.users.routers import login_router, users_router
from fastapi_mongodb.db import db_handler

__all__ = ["App"]


App = fastapi.FastAPI(
    version="0.0.1",
    debug=settings.Settings.DEBUG,
    title=settings.Settings.PROJECT_NAME,
    docs_url="/docs/",
    redoc_url="/redoc/",
    servers=[
        {"url": "", "description": "Local Development Server"},
        {"url": "https://dev.example.com", "description": "Development Server"},
    ],
    description="Quick start FastAPI project template",
    default_response_class=fastapi.responses.ORJSONResponse,
    on_startup=[db_handler.create_client],
    on_shutdown=[db_handler.delete_client],
)


# Append middlewares to 'stack' (first added -> last called)
App.add_middleware(
    middleware_class=AuthenticationMiddleware,
    backend=JWTTokenBackend(),
    on_error=lambda conn, exc: fastapi.responses.ORJSONResponse(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)}
    ),
)
App.add_middleware(middleware_class=DBSessionMiddleware)
App.add_middleware(
    middleware_class=fastapi.middleware.cors.CORSMiddleware,
    allow_origins=settings.Settings.ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
App.add_middleware(middleware_class=ExceptionsMiddleware)

# Include routers for App
App.include_router(router=users_router)
App.include_router(router=login_router)

# Add Handlers classes for global App.state
App.state.UsersHandler = UsersHandler
