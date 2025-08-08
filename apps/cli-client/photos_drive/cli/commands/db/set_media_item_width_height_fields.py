from collections import deque
import logging
from typing import cast

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
from photos_drive.shared.blob_store.gphotos.valid_file_extensions import (
    IMAGE_FILE_EXTENSIONS,
    VIDEO_FILE_EXTENSIONS,
)
from photos_drive.shared.metadata.album_id import AlbumId
from photos_drive.shared.metadata.media_items_repository import (
    FindMediaItemRequest,
    UpdateMediaItemRequest,
)
from photos_drive.shared.metadata.mongodb.albums_repository_impl import (
    AlbumsRepositoryImpl,
)
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.mongodb.media_items_repository_impl import (
    MediaItemsRepositoryImpl,
)
from photos_drive.shared.utils.dimensions.cv2_video_dimensions import (
    get_width_height_of_video,
)
from photos_drive.shared.utils.dimensions.pillow_image_dimensions import (
    get_width_height_of_image,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def set_media_item_width_height_fields(
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
            help="Whether to rewrite all the existing width and height data",
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
        "Called db set-media-item-width-height-fields handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" rewrite={rewrite}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
    albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
    media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

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

                if not rewrite and media_item.width != 0 and media_item.height != 0:
                    continue

                try:
                    width, height = None, None
                    if file_path.lower().endswith(IMAGE_FILE_EXTENSIONS):
                        width, height = get_width_height_of_image(file_path)
                    elif file_path.lower().endswith(VIDEO_FILE_EXTENSIONS):
                        width, height = get_width_height_of_video(file_path)
                    else:
                        raise ValueError(f'{file_path} is not image or video')
                except Exception as e:
                    print(f"get_width_height() error for {file_path}:")
                    print(e)
                    continue

                print(f'{file_path}: {width}x{height}')

                update_media_item_requests.append(
                    UpdateMediaItemRequest(
                        media_item_id=media_item.id,
                        new_width=width,
                        new_height=height,
                    )
                )

    if prompt_user_for_yes_no_answer('Is this correct? [Y/N]:'):
        media_items_repo.update_many_media_items(update_media_item_requests)
    else:
        print("Operation cancelled")
