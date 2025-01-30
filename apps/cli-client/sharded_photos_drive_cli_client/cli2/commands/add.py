from typing import cast
from typing_extensions import Annotated
import typer
from pymongo import MongoClient

from sharded_photos_drive_cli_client.shared.config.config import Config
from sharded_photos_drive_cli_client.shared.config.config_from_file import (
    ConfigFromFile,
)
from sharded_photos_drive_cli_client.shared.config.config_from_mongodb import (
    ConfigFromMongoDb,
)

app = typer.Typer()


@app.callback()
def config_callback(
    ctx: typer.Context,
    config_file: Annotated[
        str | None,
        typer.Option(
            "--config-file",
            help="Path to config file",
            is_eager=False,
        ),
    ] = None,
    config_mongodb: Annotated[
        str | None,
        typer.Option(
            "--config-mongodb",
            help="Connection string to a MongoDB account that has the configs",
            is_eager=False,
        ),
    ] = None,
):
    print(config_file, config_mongodb)
    if config_file:
        ctx.obj['config'] = cast(Config, ConfigFromFile(config_file))
    elif config_mongodb:
        ctx.obj['config'] = cast(Config, ConfigFromMongoDb(MongoClient(config_mongodb)))
    else:
        raise ValueError('Need to specify either --config-mongodb or --config-file')


@app.command()
def add(ctx: typer.Context):
    print("add files handler")
    print(ctx)
