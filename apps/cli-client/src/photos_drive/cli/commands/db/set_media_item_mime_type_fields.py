import magic
from collections import deque
from datetime import datetime
import logging
from typing import cast

from exiftool import ExifToolHelper
from tqdm import tqdm
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
from photos_drive.shared.core.albums.album_id import AlbumId
from photos_drive.shared.core.albums.repository.union import (
    create_union_albums_repository_from_db_clients,
)
from photos_drive.shared.core.databases.mongodb import (
    MongoDBClientsRepository,
)
from photos_drive.shared.core.media_items.repository.base import (
    FindMediaItemRequest,
    UpdateMediaItemRequest,
)
from photos_drive.shared.core.media_items.repository.union import (
    create_union_media_items_repository_from_db_clients,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def set_media_item_mime_type_fields(
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
    rewrite: Annotated[
        bool,
        typer.Option(
            "--rewrite",
            help="Whether to rewrite all the existing date_taken data",
        ),
    ] = False,
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
        "Called db set-media-item-mime-type-fields handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" rewrite={rewrite}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    mongodb_clients_repo = MongoDBClientsRepository.build_from_config(config)
    albums_repo = create_union_albums_repository_from_db_clients(mongodb_clients_repo)
    media_items_repo = create_union_media_items_repository_from_db_clients(
        mongodb_clients_repo
    )

    update_media_item_requests: list[UpdateMediaItemRequest] = []
    root_album_id = config.get_root_album_id()
    albums_queue: deque[tuple[AlbumId, list[str]]] = deque([(root_album_id, [])])

    with tqdm(desc="Finding media items") as pbar:
        while len(albums_queue) > 0:
            album_id, prev_albums_path = albums_queue.popleft()
            album = albums_repo.get_album_by_id(album_id)

            for child_album in albums_repo.find_child_albums(album.id):
                if album_id == root_album_id:
                    albums_queue.append((child_album.id, prev_albums_path + ['.']))
                else:
                    albums_queue.append(
                        (child_album.id, prev_albums_path + [cast(str, album.name)])
                    )

            for media_item in media_items_repo.find_media_items(
                FindMediaItemRequest(album_id=album_id)
            ):
                if album_id == root_album_id:
                    file_path = '/'.join(prev_albums_path + [media_item.file_name])
                else:
                    file_path = '/'.join(
                        prev_albums_path + [cast(str, album.name), media_item.file_name]
                    )
                pbar.update(1)

                if not rewrite and media_item.mime_type != "application/octet-stream":
                    continue

                try:
                    mime_type = get_mime_type(file_path)
                except Exception as e:
                    print(f"get_mime_type() error for {file_path}:")
                    print(e)
                    continue

                print(f'{file_path} type: {mime_type}')

                update_media_item_requests.append(
                    UpdateMediaItemRequest(
                        media_item_id=media_item.id,
                        new_mime_type=mime_type,
                    )
                )

    if prompt_user_for_yes_no_answer('Is this correct? [Y/N]:'):
        media_items_repo.update_many_media_items(update_media_item_requests)
    else:
        print("Operation cancelled")


def get_mime_type(file_path: str) -> str:
    return magic.from_file(file_path, mime=True) or "application/octet-stream"
