import pymongo
import typer

from apps.common.db import make_collection, make_indexes
from apps.common.utils import MakeAsync
from apps.users.config import users_settings

__all__ = ["users_commands"]


users_commands = typer.Typer(name="users")


async def setup_app():
    await make_collection(col_name=users_settings.USERS_COL)

    indexes = [pymongo.IndexModel(keys=[("email", pymongo.ASCENDING)], name="email", unique=True)]
    result = await make_indexes(col_name=users_settings.USERS_COL, indexes=indexes)
    for index_name in result:
        typer.secho(message=f"Index: '{index_name}' created successfully.", fg=typer.colors.GREEN)


@users_commands.command(name="setup")
@MakeAsync()
async def setup():
    await setup_app()
