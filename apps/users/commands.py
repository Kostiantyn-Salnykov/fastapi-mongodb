import pymongo
import typer

from apps.users.config import users_settings
from bases.db import db_handler
from bases.helpers import MakeAsync

__all__ = ["users_commands"]

users_commands = typer.Typer(name="users")


async def setup_app():
    await db_handler.create_collection(name=users_settings.USERS_COL)

    indexes = [
        pymongo.IndexModel(
            keys=[("email", pymongo.ASCENDING)],
            name="email",
            unique=True,
            background=True,
        )
    ]
    result = await db_handler.create_indexes(col_name=users_settings.USERS_COL, indexes=indexes)
    for index_name in result:
        typer.secho(
            message=f"Index: '{index_name}' for collection '{users_settings.USERS_COL}' created successfully.",
            fg=typer.colors.GREEN,
        )


@users_commands.command(name="setup")
@MakeAsync()
async def setup():
    await setup_app()
