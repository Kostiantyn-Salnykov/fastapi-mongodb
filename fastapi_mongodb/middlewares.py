"""Application middleware classes"""

import fastapi
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint, DispatchFunction
from starlette.types import ASGIApp

from fastapi_mongodb.db import BaseDBManager

__all__ = ["DBSessionMiddleware"]


class DBSessionMiddleware(BaseHTTPMiddleware):
    """Append 'db_session' for every request.state"""

    def __init__(self, app: ASGIApp, db_manager: BaseDBManager, dispatch: DispatchFunction = None) -> None:
        self.app = app
        self.db_manager = db_manager
        self.dispatch_func = self.dispatch if dispatch is None else dispatch

    async def dispatch(self, request: fastapi.Request, call_next: RequestResponseEndpoint) -> fastapi.Response:
        db_client = self.db_manager.retrieve_client()
        async with await db_client.start_session() as session:
            request.state.db_session = session
            return await call_next(request)
