import logging
from bson import ObjectId
from typing_extensions import Annotated
import typer
from google.oauth2.credentials import Credentials

from sharded_photos_drive_cli_client.cli2.shared.inputs import (
    READ_ONLY_SCOPES,
    READ_WRITE_SCOPES,
    prompt_user_for_gphotos_credentials,
    prompt_user_for_mongodb_connection_string,
    prompt_user_for_non_empty_input_string,
    prompt_user_for_yes_no_answer,
)
from sharded_photos_drive_cli_client.cli2.shared.config import build_config_from_options
from sharded_photos_drive_cli_client.cli2.shared.logging import setup_logging
from sharded_photos_drive_cli_client.cli2.shared.typer import (
    createMutuallyExclusiveGroup,
)
from sharded_photos_drive_cli_client.shared.config.config import (
    UpdateGPhotosConfigRequest,
    UpdateMongoDbConfigRequest,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def gphotos(
    id: str,
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
        "Called config reauthorize gphotos handler with args:\n"
        + f" id: {id}\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    id_obj = ObjectId(id)
    cur_config = next(filter(lambda x: x.id == id_obj, config.get_gphotos_configs()))
    new_name = __get_new_name(cur_config.name)
    new_read_write_credentials = __get_new_read_write_credentials()
    new_read_only_credentials = __get_new_read_only_credentials()

    has_change = (
        new_name is not None
        and new_read_write_credentials is not None
        and new_read_only_credentials is not None
    )

    if has_change:
        config.update_gphotos_config(
            UpdateGPhotosConfigRequest(
                id=id_obj,
                new_name=new_name,
                new_read_write_credentials=new_read_write_credentials,
                new_read_only_credentials=new_read_only_credentials,
            )
        )
        print(f"Successfully updated gphotos config {id}")
    else:
        print("No change")


@app.command()
def mongodb(
    id: str,
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
        "Called config reauthorize mongodb handler with args:\n"
        + f" id: {id}\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    id_obj = ObjectId(id)
    config = build_config_from_options(config_file, config_mongodb)
    cur_config = next(filter(lambda x: x.id == id_obj, config.get_mongodb_configs()))
    new_name = __get_new_name(cur_config.name)
    new_read_write_connection_string = __get_new_read_write_connection_string()
    new_read_only_connection_string = __get_new_read_only_connection_string()

    has_change = (
        new_name is not None
        and new_read_write_connection_string is not None
        and new_read_only_connection_string is not None
    )

    if has_change:
        config.update_mongodb_config(
            UpdateMongoDbConfigRequest(
                id=id_obj,
                new_name=new_name,
                new_read_write_connection_string=new_read_write_connection_string,
                new_read_only_connection_string=new_read_only_connection_string,
            )
        )
        print(f"Successfully updated mongodb config {id}")
    else:
        print("No change")


def __get_new_name(cur_name: str) -> str | None:
    print(f"The account name is {cur_name}")
    if not prompt_user_for_yes_no_answer("Do you want to change the name? (Y/N): "):
        return None

    return prompt_user_for_non_empty_input_string("Enter new name: ")


def __get_new_read_write_credentials() -> Credentials | None:
    if not prompt_user_for_yes_no_answer(
        "Do you want to change the read+write credentials? (Y/N): "
    ):
        return None

    return prompt_user_for_gphotos_credentials(READ_WRITE_SCOPES)


def __get_new_read_only_credentials() -> Credentials | None:
    if not prompt_user_for_yes_no_answer(
        "Do you want to change the read-only credentials? (Y/N): "
    ):
        return None

    return prompt_user_for_gphotos_credentials(READ_ONLY_SCOPES)


def __get_new_read_write_connection_string() -> str | None:
    if not prompt_user_for_yes_no_answer(
        "Do you want to change the read+write connection string? (Y/N): "
    ):
        return None

    return prompt_user_for_mongodb_connection_string(
        "Enter your new read+write connection string: "
    )


def __get_new_read_only_connection_string() -> str | None:
    if not prompt_user_for_yes_no_answer(
        "Do you want to change the read+only connection string? (Y/N): "
    ):
        return None

    return prompt_user_for_mongodb_connection_string(
        "Enter your new read+only connection string: "
    )
