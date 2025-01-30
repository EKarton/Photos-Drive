import functools
from typing import Callable, cast
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


def add_config_options(func: Callable):
    @typer.option(
        "--config-file",
        help="Path to config file",
        is_eager=False,
    )
    @typer.option(
        "--config-mongodb",
        help="MongoDB connection string",
        is_eager=False,
    )
    @functools.wraps(func)  # Preserve metadata
    def wrapper(
        ctx: typer.Context,
        config_file: str | None = None,  # These arguments are now added
        config_mongodb: str | None = None,
        *args,
        **kwargs,
    ):
        return func(ctx, config_file, config_mongodb, *args, **kwargs)

    return wrapper


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
