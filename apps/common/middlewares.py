"""Application middleware classes"""
from fastapi import Request, Response, responses, status
from pymongo.errors import DuplicateKeyError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from apps.common.db import get_mongo_client
from apps.common.exceptions import NotFoundHandlerException, HandlerException, RepositoryException
from apps.common.logging import logger


class MongoSessionMiddleware(BaseHTTPMiddleware):
    """Append 'mongo_session' for every request.state"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        mongo_client = get_mongo_client()
        async with await mongo_client.start_session() as session:
            request.state.mongo_session = session
            return await call_next(request)


class ExceptionsMiddleware(BaseHTTPMiddleware):
    """Middleware that handle default application exceptions"""

    async def dispatch(self, request, call_next) -> Response:
        try:
            response = await call_next(request)
        except NotFoundHandlerException as error:
            return responses.ORJSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(error)})
        except HandlerException as error:
            return responses.ORJSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(error)})
        except DuplicateKeyError as error:
            return responses.ORJSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": error.details})
        except RepositoryException as error:
            return responses.ORJSONResponse(status_code=error.status_code, content={"detail": error.detail})
        except Exception as error:
            logger.error(msg=f"HandlerExceptionsMiddleware | Exception | {error}")
            return responses.ORJSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": str(error)}
            )
        else:
            return response
