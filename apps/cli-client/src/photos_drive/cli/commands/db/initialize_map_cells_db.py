import logging

import typer
from typing_extensions import Annotated

from photos_drive.cli.shared.config import build_config_from_options
from photos_drive.cli.shared.logging import setup_logging
from photos_drive.cli.shared.typer import (
    createMutuallyExclusiveGroup,
)
from photos_drive.shared.core.databases.mongodb import (
    MongoDBClientsRepository,
)
from photos_drive.shared.core.media_items.repository.mongodb import (
    MongoDBMediaItemsRepository,
)
from photos_drive.shared.core.media_items.repository.union import (
    UnionMediaItemsRepository,
)
from photos_drive.shared.features.maps.repository.mongodb import (
    MongoDBMapCellsRepository,
)
from photos_drive.shared.features.maps.repository.union import (
    UnionMapCellsRepository,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def initialize_map_cells_db(
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
        "Called db initialize-map-cells-db handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    transaction_repository = MongoDBClientsRepository.build_from_config(config)

    for _, client in transaction_repository.get_all_clients():
        client['photos_drive']['tiles'].delete_many({})
        client['photos_drive']['map_cells'].create_index(
            [("cell_id", 1), ("album_id", 1), ("media_item_id", 1)]
        )

    media_items_repo = UnionMediaItemsRepository(
        [
            MongoDBMediaItemsRepository(client_id, client, transaction_repository)
            for (client_id, client) in transaction_repository.get_all_clients()
        ]
    )
    tiles_repo = UnionMapCellsRepository(
        [
            MongoDBMapCellsRepository(client_id, client, transaction_repository)
            for (client_id, client) in transaction_repository.get_all_clients()
        ]
    )
    for media_item in media_items_repo.get_all_media_items():
        if media_item.location is not None:
            tiles_repo.add_media_item(media_item)
            print(f'Added media item {media_item.id}')
