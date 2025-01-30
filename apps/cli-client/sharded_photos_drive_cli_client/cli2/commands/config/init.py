import logging
import os
from typing_extensions import Annotated
import typer
from pymongo import MongoClient

from sharded_photos_drive_cli_client.cli2.shared.inputs import (
    READ_ONLY_SCOPES,
    prompt_user_for_gphotos_credentials,
    prompt_user_for_mongodb_connection_string,
)
from sharded_photos_drive_cli_client.cli2.shared.logging import setup_logging
from sharded_photos_drive_cli_client.shared.config.config import (
    AddGPhotosConfigRequest,
    AddMongoDbConfigRequest,
    Config,
)
from sharded_photos_drive_cli_client.shared.config.config_from_file import (
    ConfigFromFile,
)
from sharded_photos_drive_cli_client.shared.config.config_from_mongodb import (
    ConfigFromMongoDb,
)
from sharded_photos_drive_cli_client.shared.mongodb.albums_repository import (
    AlbumsRepositoryImpl,
)
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
)

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command()
def init(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Whether to show all logging debug statements or not",
        ),
    ] = False,
):
    setup_logging(verbose)

    logger.debug(f"Called config init handler with args:\n verbose={verbose}")

    # Step 0: Ask where to save config
    __prompt_welcome()
    config = __prompt_config()

    # Step 1: Ask for Mongo DB account
    print("First, let's log into your first Mongo DB account.")
    mongodb_name = __get_non_empty_name_for_mongodb()

    mongodb_rw_connection_string = prompt_user_for_mongodb_connection_string(
        "Enter your read+write connection string: "
    )

    mongodb_r_connection_string = prompt_user_for_mongodb_connection_string(
        "Enter your read-only connection string: "
    )

    config.add_mongodb_config(
        AddMongoDbConfigRequest(
            name=mongodb_name,
            read_write_connection_string=mongodb_rw_connection_string,
            read_only_connection_string=mongodb_r_connection_string,
        )
    )

    # Step 2: Ask for Google Photo account
    print("Now it's time to log in to your first Google Photos account.")
    gphotos_name = __get_non_empty_name_for_gphotos()

    print("Now, time to log into your Google account for read+write access\n")
    gphotos_rw_credentials = prompt_user_for_gphotos_credentials()

    print("Now, time to log into your Google account for read-only access\n")
    gphotos_r_credentials = prompt_user_for_gphotos_credentials(READ_ONLY_SCOPES)

    config.add_gphotos_config(
        AddGPhotosConfigRequest(
            name=gphotos_name,
            read_write_credentials=gphotos_rw_credentials,
            read_only_credentials=gphotos_r_credentials,
        )
    )

    # Step 3: Create root album in Mongo DB account
    print("Perfect! Setting up your accounts...")
    mongodb_repo = MongoDbClientsRepository.build_from_config(config)
    albums_repo = AlbumsRepositoryImpl(mongodb_repo)
    root_album = albums_repo.create_album(
        album_name="", parent_album_id=None, child_album_ids=[], media_item_ids=[]
    )
    config.set_root_album_id(root_album.id)

    # Step 4: Save the config file
    if type(config) is ConfigFromFile:
        config.flush()
        print("Saved your config")

    # Step 5: Tell user how to add more MongoDB accounts / Google Photo accounts
    print(
        "Congratulations! You have set up a basic version of sharded_google_photos!\n"
        + "\n"
        + "You can always add more MongoDB accounts by:\n"
        + " 1. Create a new MongoDB account\n"
        + " 2. Run:\n"
    )

    if type(config) is ConfigFromFile:
        print(f"      {get_config_add_mongodb_config_file_cli()}")
    else:
        print(f"      {get_config_add_mongodb_config_file_cli()}")

    print(
        "\nSimilarly, you can add more Google Photos storage by: \n"
        + "  1. Create a new Google Photos account\n"
        + "  2. Run:\n"
    )
    if type(config) is ConfigFromFile:
        print(f"      {get_config_add_gphotos_config_file_cli()}")
    else:
        print(f"      {get_config_add_gphotos_config_file_cli()}")

    print("\nThat's it! Have fun uploading photos!")


def __prompt_welcome():
    print(
        "Welcome!\n"
        + "Before you get started with sharded_google_photos, you need the following:\n"
        + "\n  1. A place to store your config files (MongoDB or in a config file).\n"
        + "\n  2. A place to store your photo metadata (MongoDB).\n"
        + "\n  3. A place to store your photos (Google Photos account).\n"
        + "\n"
        + "Press [enter] to continue\n"
    )


def __prompt_config() -> Config:
    config_type = __prompt_which_config_type()
    if config_type == 'mongodb':
        return __prompt_mongodb_config()
    elif config_type == 'file':
        return __prompt_config_file()
    else:
        raise ValueError(f"Unknown config type {config_type}")


def __prompt_which_config_type() -> str:
    while True:
        print("Where do you want to store your config?")
        print("\n  1. Mongo DB (mongodb)")
        print("\n  2. File (file)")
        print(
            "\nThe config saves the accounts of where your photos metadata are, and"
            "\nthe accounts of where your photos are"
            "\n"
        )

        raw_input = input("Enter your choice:")
        user_input = raw_input.strip().lower()

        if user_input in ["mongodb", "1"]:
            return 'mongodb'
        elif user_input in ["file", "2"]:
            return 'file'
        else:
            print("Invalid input. Please enter \'mongodb\' or \'file\'")


def __prompt_mongodb_config() -> ConfigFromMongoDb:
    connection_string = prompt_user_for_mongodb_connection_string(
        "Enter your read+write connection string: "
    )
    return ConfigFromMongoDb(MongoClient(connection_string))


def __prompt_config_file() -> ConfigFromFile:
    while True:
        file_name = input("Enter file name:")
        file_path = os.path.join(os.getcwd(), file_name)

        if os.path.exists(file_path):
            print("File name already exists. Please try another file name.")
        else:
            return ConfigFromFile(file_path)


def __get_non_empty_name_for_mongodb() -> str:
    """Prompts the user for a name and ensures it's not empty."""

    while True:
        name = input("Enter name of your first Mongo DB account: ")
        stripped_name = name.strip()

        if not stripped_name:
            print("Name cannot be empty. Please try again.")

        else:
            return stripped_name


def __get_non_empty_name_for_gphotos() -> str:
    """Prompts the user for a name and ensures it's not empty."""

    while True:
        print(
            "Enter name of your first Google Photos account "
            + "(could be email address): "
        )
        name = input()
        stripped_name = name.strip()

        if not stripped_name:
            print("Name cannot be empty. Please try again.")

        else:
            return stripped_name


def get_config_add_gphotos_config_file_cli():
    return "sharded_google_photos config add gphotos --config-file <file-path>"


def get_config_add_mongodb_config_file_cli():
    return "sharded_google_photos config add mongodb --config-file <file-path>"


def get_config_add_gphotos_config_mongodb_cli():
    return "sharded_google_photos config add gphotos --config-mongodb <file-path>"


def get_config_add_mongodb_config_mongodb_cli():
    return "sharded_google_photos config add mongodb --config-mongodb <file-path>"
