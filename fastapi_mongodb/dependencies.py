import fastapi

import fastapi_mongodb.db
import pymongo.client_session


__all__ = ["DBSession"]


class DBSession:
    def __init__(self, db_manager: fastapi_mongodb.db.BaseDBManager = None, state_attr_name: str = "db_manager"):
        self.db_manager = db_manager
        self.state_attr_name = state_attr_name

    async def __call__(self, request: fastapi.Request) -> pymongo.client_session.ClientSession:
        db_manager = self.db_manager or getattr(request.app.state, self.state_attr_name, None)
        if not db_manager:
            raise NotImplementedError(
                "Provide 'db_manager' parameter to dependency initializer OR set '<FastAPI APP>.state.db_manager' "
                "to global app state"
            )
        db_client = db_manager.retrieve_client()
        async with await db_client.start_session() as session:
            yield session
