import logging

import typer
from typing_extensions import Annotated

from photos_drive.cli.shared.config import build_config_from_options
from photos_drive.cli.shared.inputs import (
    prompt_user_for_yes_no_answer,
)
from photos_drive.cli.shared.logging import setup_logging
from photos_drive.cli.shared.typer import (
    createMutuallyExclusiveGroup,
)
from photos_drive.shared.blob_store.gphotos.client import GPhotosClientV2
from photos_drive.shared.blob_store.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def teardown(
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

    if not prompt_user_for_yes_no_answer(
        "Do you want to delete everything this tool has ever created? (Y/N): "
    ):
        return

    config = build_config_from_options(config_file, config_mongodb)
    mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
    gphoto_clients_repo = GPhotosClientsRepository.build_from_config(config)
    root_album_id = config.get_root_album_id()

    # Delete all albums from DB except for the root album
    for id, client in mongodb_clients_repo.get_all_clients():
        if root_album_id.client_id == id:
            client["photos_drive"]["albums"].delete_many(
                {"_id": {"$ne": root_album_id.object_id}}
            )
        else:
            client["photos_drive"]["albums"].delete_many({})

    # Delete all media items from the DB
    for _, client in mongodb_clients_repo.get_all_clients():
        client["photos_drive"]["media_items"].delete_many({})

    # Put all the photos that Google Photos has uploaded into a folder
    # called 'To delete'
    for _, gphotos_client in gphoto_clients_repo.get_all_clients():
        trash_album_id: str | None = None
        for album in gphotos_client.albums().list_albums():
            if album.title == "To delete":
                trash_album_id = album.id
                break

        if not trash_album_id:
            trash_album_id = gphotos_client.albums().create_album("To delete").id

        media_item_ids = [
            m.id for m in gphotos_client.media_items().search_for_media_items()
        ]
        if len(media_item_ids) > 0:
            __add_media_items_to_album_safely(
                gphotos_client, trash_album_id, media_item_ids
            )


def __add_media_items_to_album_safely(
    client: GPhotosClientV2, album_id: str, media_item_ids: list[str]
):
    MAX_UPLOAD_TOKEN_LENGTH_PER_CALL = 50

    for i in range(0, len(media_item_ids), MAX_UPLOAD_TOKEN_LENGTH_PER_CALL):
        chunked_media_item_ids = media_item_ids[
            i : i + MAX_UPLOAD_TOKEN_LENGTH_PER_CALL
        ]
        client.albums().add_photos_to_album(album_id, chunked_media_item_ids)
