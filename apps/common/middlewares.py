"""Application middleware classes"""
import sys
import traceback

import fastapi
import pymongo.errors
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

import settings
from fastapi_mongodb.db import db_handler
from fastapi_mongodb.exceptions import (
    HandlerException,
    NotFoundHandlerException,
    PermissionException,
    RepositoryException,
)
from fastapi_mongodb.logging import logger


class DBSessionMiddleware(BaseHTTPMiddleware):
    """Append 'db_session' for every request.state"""

    async def dispatch(self, request: fastapi.Request, call_next: RequestResponseEndpoint) -> fastapi.Response:
        db_client = db_handler.retrieve_client()
        async with await db_client.start_session() as session:
            request.state.db_session = session
            return await call_next(request)


class ExceptionsMiddleware(BaseHTTPMiddleware):
    """Middleware that handle default application exceptions"""

    async def dispatch(self, request, call_next) -> fastapi.Response:
        try:
            response = await call_next(request)
        except NotFoundHandlerException as error:
            return fastapi.responses.ORJSONResponse(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
                content={"detail": str(error)},
            )
        except HandlerException as error:
            return fastapi.responses.ORJSONResponse(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST,
                content={"detail": str(error)},
            )
        except pymongo.errors.DuplicateKeyError as error:
            return fastapi.responses.ORJSONResponse(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST,
                content={"detail": error.details},
            )
        except RepositoryException as error:
            return fastapi.responses.ORJSONResponse(status_code=error.status_code, content={"detail": error.detail})
        except PermissionException as error:
            return fastapi.responses.ORJSONResponse(status_code=error.status_code, content={"detail": error.detail})
        except Exception as error:
            logger.error(msg=f"HandlerExceptionsMiddleware | Exception | {error}")
            if settings.Settings.DEBUG:
                traceback.print_exc()
                return fastapi.responses.ORJSONResponse(
                    status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "detail": str(error),
                        "type": f"{str(error.__class__.__name__)}",
                        "traceback": traceback.format_exception(*sys.exc_info()),
                    },
                )
            else:
                return fastapi.responses.ORJSONResponse(
                    status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Please, contact site administrator and tell about this issue."},
                )
        else:
            return response
