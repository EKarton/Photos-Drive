import logging
from typing_extensions import Annotated
import typer

from sharded_photos_drive_cli_client.cli2.shared.inputs import (
    READ_ONLY_SCOPES,
    prompt_user_for_gphotos_credentials,
    prompt_user_for_mongodb_connection_string,
    prompt_user_for_non_empty_input_string,
)
from sharded_photos_drive_cli_client.cli2.shared.config import build_config_from_options
from sharded_photos_drive_cli_client.cli2.shared.logging import setup_logging
from sharded_photos_drive_cli_client.cli2.shared.typer import (
    createMutuallyExclusiveGroup,
)
from sharded_photos_drive_cli_client.shared.config.config import (
    AddGPhotosConfigRequest,
    AddMongoDbConfigRequest,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def gphotos(
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
        "Called config add gphotos handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    gphotos_account_name = prompt_user_for_non_empty_input_string(
        "Enter name of your Google Photos account: "
    )

    print("Now, time to log into your Google account for read+write access\n")
    read_write_credentials = prompt_user_for_gphotos_credentials()

    print("Now, time to log into your Google account for read only access\n")
    read_only_credentials = prompt_user_for_gphotos_credentials(READ_ONLY_SCOPES)

    config.add_gphotos_config(
        AddGPhotosConfigRequest(
            name=gphotos_account_name,
            read_write_credentials=read_write_credentials,
            read_only_credentials=read_only_credentials,
        )
    )

    print("Successfully added your Google Photos account!")


@app.command()
def mongodb(
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
        "Called config add mongodb handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    name = prompt_user_for_non_empty_input_string(
        "Enter name of your Mongo DB account: "
    )

    read_write_connection_string = prompt_user_for_mongodb_connection_string(
        "Enter your read+write connection string: "
    )

    read_only_connection_string = prompt_user_for_mongodb_connection_string(
        "Enter your read only connection string: "
    )

    config.add_mongodb_config(
        AddMongoDbConfigRequest(
            name=name,
            read_write_connection_string=read_write_connection_string,
            read_only_connection_string=read_only_connection_string,
        )
    )

    print("Successfully added your Mongo DB account!")
