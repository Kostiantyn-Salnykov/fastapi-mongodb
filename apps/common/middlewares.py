"""Application middleware classes"""
import traceback

import fastapi
import pymongo.errors
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

import bases
import settings


class DBSessionMiddleware(BaseHTTPMiddleware):
    """Append 'db_session' for every request.state"""

    async def dispatch(self, request: fastapi.Request, call_next: RequestResponseEndpoint) -> fastapi.Response:
        db_client = bases.db.DBHandler.retrieve_client()
        async with await db_client.start_session() as session:
            request.state.db_session = session
            return await call_next(request)


class ExceptionsMiddleware(BaseHTTPMiddleware):
    """Middleware that handle default application exceptions"""

    async def dispatch(self, request, call_next) -> fastapi.Response:
        try:
            response = await call_next(request)
        except bases.exceptions.NotFoundHandlerException as error:
            return fastapi.responses.ORJSONResponse(
                status_code=fastapi.status.HTTP_404_NOT_FOUND, content={"detail": str(error)}
            )
        except bases.exceptions.HandlerException as error:
            return fastapi.responses.ORJSONResponse(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST, content={"detail": str(error)}
            )
        except pymongo.errors.DuplicateKeyError as error:
            return fastapi.responses.ORJSONResponse(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST, content={"detail": error.details}
            )
        except bases.exceptions.RepositoryException as error:
            return fastapi.responses.ORJSONResponse(status_code=error.status_code, content={"detail": error.detail})
        except bases.exceptions.PermissionException as error:
            return fastapi.responses.ORJSONResponse(status_code=error.status_code, content={"detail": error.detail})
        except Exception as error:
            bases.logging.logger.error(msg=f"HandlerExceptionsMiddleware | Exception | {error}")
            if settings.Settings.DEBUG:
                traceback.print_exc()
                return fastapi.responses.ORJSONResponse(
                    status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": str(error)}
                )
            else:
                return fastapi.responses.ORJSONResponse(
                    status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Please, contact site administrator and tell about this issue."},
                )
        else:
            return response
