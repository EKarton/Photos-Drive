import logging
from prettytable import PrettyTable
from typing_extensions import Annotated
import typer
from pymongo import MongoClient

from sharded_photos_drive_cli_client.clean.clean_system import TRASH_ALBUM_TITLE
from sharded_photos_drive_cli_client.cli2.shared.config import build_config_from_options
from sharded_photos_drive_cli_client.cli2.shared.logging import setup_logging
from sharded_photos_drive_cli_client.cli2.shared.typer import (
    createMutuallyExclusiveGroup,
)
from sharded_photos_drive_cli_client.shared.config.config import Config
from sharded_photos_drive_cli_client.shared.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    BYTES_512MB,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def usage(
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
        "Called teardown handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    config = build_config_from_options(config_file, config_mongodb)
    print(__get_mongodb_accounts_table(config))
    print("")

    gphotos_repo = GPhotosClientsRepository.build_from_config(config)
    print(__get_gphoto_clients_table(gphotos_repo))


def __get_mongodb_accounts_table(config: Config) -> PrettyTable:
    table = PrettyTable(title="MongoDB accounts")
    table.field_names = [
        "ID",
        "Name",
        "Free space remaining",
        "Usage",
        "Number of objects",
    ]
    for mongodb_config in config.get_mongodb_configs():
        client: MongoClient = MongoClient(mongodb_config.read_write_connection_string)
        db = client["sharded_google_photos"]
        db_stats = db.command({"dbStats": 1, 'freeStorage': 1})
        raw_total_free_storage = db_stats["totalFreeStorageSize"]
        usage = db_stats["storageSize"]
        num_objects = db_stats['objects']

        free_space = raw_total_free_storage
        if raw_total_free_storage == 0:
            free_space = BYTES_512MB - usage

        table.add_row(
            [mongodb_config.id, mongodb_config.name, free_space, usage, num_objects]
        )

    # Left align the columns
    for col in table.align:
        table.align[col] = "l"

    return table


def __get_gphoto_clients_table(gphotos_repo: GPhotosClientsRepository) -> PrettyTable:
    table = PrettyTable(title="Google Photos clients")
    table.field_names = [
        "ID",
        "Name",
        "Used / limit (bytes)",
        "Trash album size (photo count)",
    ]

    for client_id, client in gphotos_repo.get_all_clients():
        usage, limit = '', ''

        try:
            storage_quota = client.get_storage_quota()
            usage = str(storage_quota.usage)
            limit = str(storage_quota.limit)

            trash_album = next(
                filter(
                    lambda x: x.title == TRASH_ALBUM_TITLE,
                    client.albums().list_albums(),
                ),
                None,
            )
            num_photos_in_trash_album = (
                str(trash_album.mediaItemsCount)
                if trash_album is not None and trash_album.mediaItemsCount is not None
                else '0'
            )
        except Exception as error:
            logger.error(f'Error occurred to get details of gphotos client {client_id}')
            logger.error(error)
            usage = 'ERROR'
            limit = 'ERROR'
            num_photos_in_trash_album = 'ERROR'

        table.add_row(
            [
                client_id,
                client.name(),
                f'{usage} / {limit}',
                num_photos_in_trash_album,
            ]
        )

    # Left align the columns except for usage and trash usage
    for col in table.align:
        table.align[col] = "l"

    table.align["Used / Limit (in bytes)"] = "r"
    table.align["Amount in trash (in bytes)"] = 'r'

    return table
