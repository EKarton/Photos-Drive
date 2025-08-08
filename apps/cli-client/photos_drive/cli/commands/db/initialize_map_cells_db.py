import logging

import typer
from typing_extensions import Annotated

from photos_drive.cli.shared.config import build_config_from_options
from photos_drive.cli.shared.logging import setup_logging
from photos_drive.cli.shared.typer import (
    createMutuallyExclusiveGroup,
)
from photos_drive.shared.maps.mongodb.map_cells_repository_impl import (
    MapCellsRepositoryImpl,
)
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.mongodb.media_items_repository_impl import (
    MediaItemsRepositoryImpl,
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
    mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)

    for _, client in mongodb_clients_repo.get_all_clients():
        client['photos_drive']['tiles'].delete_many({})
        client['photos_drive']['map_cells'].create_index(
            [("cell_id", 1), ("album_id", 1), ("media_item_id", 1)]
        )

    media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
    tiles_repo = MapCellsRepositoryImpl(mongodb_clients_repo)
    for media_item in media_items_repo.get_all_media_items():
        if media_item.location is not None:
            tiles_repo.add_media_item(media_item)
            print(f'Added media item {media_item.id}')
