import logging
from typing_extensions import Annotated
import typer
import os
import shutil
import subprocess

from ...shared.config import build_config_from_options
from ...shared.logging import setup_logging
from ...shared.typer import createMutuallyExclusiveGroup

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def dump(
    folder_path: str,
    config_file: Annotated[
        str | None,
        typer.Option(
            "--config-file",
            help="Path to config file",
            callback=config_exclusivity_callback,
        ),
    ] = None,
    config_mongodb: Annotated[
        str | None,
        typer.Option(
            "--config-mongodb",
            help="Connection string to a MongoDB account that has the configs",
            is_eager=False,
            callback=config_exclusivity_callback,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Whether to show all logging debug statements or not",
        ),
    ] = False,
):
    setup_logging(verbose)
    logger.debug(
        "Called config db-dump with args:\n"
        + f" folder_path: {folder_path}\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    os.makedirs(folder_path, exist_ok=True)

    # Dump the contents of the config file
    if config_file:
        dump_config_file(config_file, folder_path)
    elif config_mongodb:
        dump_mongodb_config_file(config_mongodb, folder_path)
    else:
        raise ValueError('Unknown arg type')

    config = build_config_from_options(config_file, config_mongodb)
    for mongodb_config in config.get_mongodb_configs():
        dump_mongodb(
            mongodb_config.read_write_connection_string,
            os.path.join(folder_path, f'mongodb_{mongodb_config.id}'),
        )


def dump_config_file(config_file: str, folder_path: str):
    shutil.copy(config_file, folder_path)


def dump_mongodb_config_file(config_mongodb: str, folder_path: str):
    dump_mongodb(config_mongodb, os.path.join(folder_path, 'config'))


def dump_mongodb(mongodb_connection_string: str, folder_path: str):
    logger.debug(f"Starting mongodump to {folder_path}")
    subprocess.run(
        [
            "mongodump",
            "--uri",
            mongodb_connection_string,
            "--db",
            'sharded_google_photos',
            "--out",
            folder_path,
        ],
        check=True,
    )
    logger.debug("mongodump finished!")
