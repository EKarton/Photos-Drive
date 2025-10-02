import logging
import os

from pymongo import MongoClient
import typer
from typing_extensions import Annotated

from photos_drive.cli.shared.inputs import (
    prompt_user_for_gphotos_credentials,
    prompt_user_for_mongodb_connection_string,
    prompt_user_for_non_empty_input_string,
    prompt_user_for_options,
)
from photos_drive.cli.shared.logging import setup_logging
from photos_drive.shared.config.config import (
    AddGPhotosConfigRequest,
    AddMongoDbConfigRequest,
    AddMongoDbVectorStoreConfigRequest,
    Config,
)
from photos_drive.shared.config.config_from_file import (
    ConfigFromFile,
)
from photos_drive.shared.config.config_from_mongodb import (
    ConfigFromMongoDb,
)
from photos_drive.shared.metadata.mongodb.albums_repository_impl import (
    AlbumsRepositoryImpl,
)
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
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

    # Step 1: Ask for databases to store the Photos Metadata store and Photos Map store
    print(
        "First, let's add a database to store your photos metadata and photos map data."
    )
    metadata_db_name = prompt_user_for_non_empty_input_string(
        "Enter name of your database: "
    )
    option = prompt_user_for_options(
        "Which type of database do you want to add?", ['MongoDB']
    )
    if option == 'MongoDB':
        mongodb_rw_connection_string = prompt_user_for_mongodb_connection_string(
            "Enter your admin connection string: "
        )
        mongodb_r_connection_string = prompt_user_for_mongodb_connection_string(
            "Enter your read-only connection string: "
        )
        config.add_mongodb_config(
            AddMongoDbConfigRequest(
                name=metadata_db_name,
                read_write_connection_string=mongodb_rw_connection_string,
                read_only_connection_string=mongodb_r_connection_string,
            )
        )
    else:
        raise NotImplementedError(f'Photos account type {option} not supported')

    # Step 2: Ask for Google Photo account
    print("Next, let's add an account to store your photos.")
    photos_store_name = prompt_user_for_non_empty_input_string(
        "Enter name of your account: "
    )
    option = prompt_user_for_options(
        "Which type of account do you want to add?", ['GooglePhotos']
    )
    if option == 'GooglePhotos':
        print("Now, time to log into your Google account for read+write access\n")
        gphotos_rw_credentials = prompt_user_for_gphotos_credentials()
        config.add_gphotos_config(
            AddGPhotosConfigRequest(
                name=photos_store_name,
                read_write_credentials=gphotos_rw_credentials,
                read_only_credentials=gphotos_rw_credentials,
            )
        )
    else:
        raise NotImplementedError(f'Photos account type {option} not supported')

    # Step 3: Ask for the vector store config
    print("Now let's add a vector database to the vector store.")
    vector_store_name = prompt_user_for_non_empty_input_string(
        "Enter name of your vector database: "
    )
    option = prompt_user_for_options(
        "Which type of database do you want to add?", ['MongoDB']
    )
    if option == 'MongoDB':
        mongodb_rw_connection_string = prompt_user_for_mongodb_connection_string(
            "Enter your admin connection string: "
        )
        mongodb_r_connection_string = prompt_user_for_mongodb_connection_string(
            "Enter your read-only connection string: "
        )

        config.add_vector_store_config(
            AddMongoDbVectorStoreConfigRequest(
                name=vector_store_name,
                read_write_connection_string=mongodb_rw_connection_string,
                read_only_connection_string=mongodb_r_connection_string,
            )
        )
    else:
        raise NotImplementedError(f'Vector database type {option} not supported')

    # Step 3: Create root album
    print("Perfect! Setting up your accounts...")
    mongodb_repo = MongoDbClientsRepository.build_from_config(config)
    albums_repo = AlbumsRepositoryImpl(mongodb_repo)
    root_album = albums_repo.create_album(album_name="", parent_album_id=None)
    config.set_root_album_id(root_album.id)

    # Step 4: Save the config file
    if type(config) is ConfigFromFile:
        config.flush()
        print("Saved your config")

    print("Congratulations! You have set up a basic version of Photos Drive!")


def __prompt_welcome():
    print(
        "Welcome!\n"
        + "Before you get started with photos_drive_cli, you need the following:\n"
        + "\n  1. A place to store your config files (MongoDB or in a config file).\n"
        + "\n  2. A place to store your photos metadata (MongoDB).\n"
        + "\n  3. A place to store your photos (Google Photos account).\n"
        + "\n  4. A place to store your photos map data (MongoDB).\n"
        + "\n  5. A place to store your photo embeddings (MongoDB).\n"
    )
    input("Press [enter] to continue")


def __prompt_config() -> Config:
    option = prompt_user_for_options(
        "Where do you want to store your configs?", ['MongoDB', 'File']
    )
    if option == 'MongoDB':
        return __prompt_mongodb_config()
    elif option == 'File':
        return __prompt_config_file()
    else:
        raise ValueError(f"Unknown config type {option}")


def __prompt_mongodb_config() -> ConfigFromMongoDb:
    connection_string = prompt_user_for_mongodb_connection_string(
        "Enter your admin connection string: "
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
