import importlib.util

import pydantic
import typer

import bases
from apps.users.commands import users_commands
from settings import settings

app = typer.Typer(name="FastAPI commands")
app.add_typer(typer_instance=users_commands)


@app.command(name="setup_apps")
@bases.helpers.MakeAsync()
async def setup_apps():
    apps_directory = settings.BASE_DIR / "apps"
    if apps_directory.is_dir():
        for application in apps_directory.iterdir():
            if application.is_dir():
                for file in application.iterdir():
                    if file.is_file() and file.name == "commands.py":
                        module_spec = importlib.util.spec_from_file_location(
                            name="commands.py spec", location=file.resolve()
                        )
                        commands_py = importlib.util.module_from_spec(spec=module_spec)
                        module_spec.loader.exec_module(commands_py)
                        await commands_py.setup_app()


@app.command(name="createapp")
@bases.helpers.MakeAsync()
async def creteapp():
    apps_directory = settings.BASE_DIR / "apps"

    app_name: str = (typer.prompt(text="Enter name of application", type=str)).lower()
    capitalized_app_name = app_name.capitalize()
    upper_app_name = app_name.upper()

    class AppFile(pydantic.BaseModel):
        file_name: str
        path: list[str]
        content: str

    files_to_create = [
        AppFile(file_name="__init__.py", path=[app_name], content=""),
        AppFile(
            file_name="config.py",
            path=[app_name],
            content=f"""import pydantic
import functools


__all__ = ["{app_name}_settings"]


class {capitalized_app_name}Settings(pydantic.BaseSettings):
    {upper_app_name}_COL: str = pydantic.Field(default="{app_name}")


@functools.lru_cache()
def get_settings() -> {capitalized_app_name}Settings:
    return {capitalized_app_name}Settings()


{app_name}_settings: {capitalized_app_name}Settings = get_settings()
""",
        ),
        AppFile(
            file_name="commands.py",
            path=[app_name],
            content=f"""import typer

import bases
from apps.{app_name}.config import {app_name}_settings

__all__ = ["{app_name}_commands"]


{app_name}_commands = typer.Typer(name="{app_name}")


async def setup_app():
    await bases.db.MongoDBConnection.create_collection(name={app_name}_settings.{upper_app_name}_COL)


@{app_name}_commands.command(name="setup")
@bases.helpers.MakeAsync()
async def setup():
    await setup_app()
""",
        ),
        AppFile(file_name="models.py", path=[app_name], content=""),
        AppFile(file_name="handlers.py", path=[app_name], content=""),
        AppFile(file_name="routers.py", path=[app_name], content=""),
        AppFile(file_name="schemas.py", path=[app_name], content=""),
        AppFile(file_name="__init__.py", path=[app_name, "tests"], content=""),
    ]

    for file in files_to_create:
        new_app_dir = apps_directory.joinpath(*file.path)
        new_file_path = new_app_dir.joinpath(file.file_name)

        if not new_app_dir.exists():
            new_app_dir.mkdir()

        if not new_file_path.exists():
            with open(file=new_file_path, mode="w") as write_file:
                write_file.write(file.content)

    typer.secho(message=f"Application '{app_name}' has been created.", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
