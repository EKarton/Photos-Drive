from dataclasses import asdict
import logging

from rich import print as richPrint
from rich.pretty import Pretty
import typer
from typing_extensions import Annotated

from photos_drive.cli.shared.config import build_config_from_options
from photos_drive.cli.shared.logging import setup_logging
from photos_drive.cli.shared.typer import (
    createMutuallyExclusiveGroup,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def view(
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
        "Called config view with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    config = build_config_from_options(config_file, config_mongodb)

    print("Metadata and Maps Database accounts:")
    for mongoDbConfig in config.get_mongodb_configs():
        richPrint(Pretty(asdict(mongoDbConfig)))

    print("Photo accounts:")
    for gPhotosConfig in config.get_gphotos_configs():
        richPrint(Pretty(asdict(gPhotosConfig)))

    print("Vector Database accounts")
    for vectorStoreConfig in config.get_vector_store_configs():
        richPrint(Pretty(asdict(vectorStoreConfig)))
