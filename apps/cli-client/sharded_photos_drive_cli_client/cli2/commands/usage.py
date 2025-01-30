import logging
from prettytable import PrettyTable
from typing_extensions import Annotated
import typer
from pymongo import MongoClient

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

    gphotos_repo = GPhotosClientsRepository.build_from_config_repo(config)
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
        "Free space remaining",
        "Amount in trash",
        "Usage",
    ]

    for client_id, client in gphotos_repo.get_all_clients():
        storage_quota = client.get_storage_quota()
        table.add_row(
            [
                client_id,
                client.name(),
                storage_quota.usage,
                storage_quota.usage_in_drive_trash,
                storage_quota.limit,
            ]
        )

    # Left align the columns
    for col in table.align:
        table.align[col] = "l"

    return table
