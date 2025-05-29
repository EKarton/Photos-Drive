from collections import deque
import logging
from typing_extensions import Annotated
import typer

from ..shared.config import build_config_from_options
from ..shared.logging import setup_logging
from ..shared.typer import createMutuallyExclusiveGroup
from ...shared.mongodb.albums_repository import AlbumsRepositoryImpl
from ...shared.mongodb.clients_repository import MongoDbClientsRepository
from ...shared.mongodb.media_items_repository import (
    MediaItemsRepositoryImpl,
    UpdateMediaItemRequest,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def add_album_id_fields_to_media_items(
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
        "Called add album id fields to media items handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
    albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
    media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

    # Do BFS and update all of the media items that exists
    update_requests = []
    queue = deque([config.get_root_album_id()])
    while len(queue) > 0:
        album_id = queue.pop()
        album = albums_repo.get_album_by_id(album_id)

        for media_item_id in album.media_item_ids:
            update_requests.append(
                UpdateMediaItemRequest(
                    media_item_id=media_item_id,
                    new_album_id=album_id,
                )
            )

        for child_album_id in album.child_album_ids:
            queue.append(child_album_id)

    logger.debug(update_requests)

    media_items_repo.update_many_media_items(update_requests)
