import pymongo
import typer

import bases.db
import bases.utils
from apps.users.config import users_settings

__all__ = ["users_commands"]


users_commands = typer.Typer(name="users")


async def setup_app():
    await bases.db.MongoDBConnection.make_collection(col_name=users_settings.USERS_COL)

    indexes = [pymongo.IndexModel(keys=[("email", pymongo.ASCENDING)], name="email", unique=True)]
    result = await bases.db.MongoDBConnection.make_indexes(col_name=users_settings.USERS_COL, indexes=indexes)
    for index_name in result:
        typer.secho(message=f"Index: '{index_name}' created successfully.", fg=typer.colors.GREEN)


@users_commands.command(name="setup")
@bases.utils.MakeAsync()
async def setup():
    await setup_app()
