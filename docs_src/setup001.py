import fastapi

import fastapi_mongodb

db_manager = fastapi_mongodb.BaseDBManager(
    db_url="mongodb://0.0.0.0:27017/", default_db_name="test_db"
)

app = fastapi.FastAPI(
    on_startup=[db_manager.create_client],
    on_shutdown=[db_manager.delete_client],
)

app.state.db_manager = db_manager
app.state.users_repository = fastapi_mongodb.BaseRepository(
    db_manager=db_manager, db_name="test_db", col_name="users"
)
