from collections import deque
from datetime import datetime
import logging
from typing import cast
from typing_extensions import Annotated
import typer
from exiftool import ExifToolHelper

from sharded_photos_drive_cli_client.cli2.shared.config import build_config_from_options
from sharded_photos_drive_cli_client.cli2.shared.inputs import (
    prompt_user_for_yes_no_answer,
)
from sharded_photos_drive_cli_client.cli2.shared.logging import setup_logging
from sharded_photos_drive_cli_client.cli2.shared.typer import (
    createMutuallyExclusiveGroup,
)
from sharded_photos_drive_cli_client.shared.dimensions.cv2_video_dimensions import (
    get_width_height_of_video,
)
from sharded_photos_drive_cli_client.shared.dimensions.pillow_image_dimensions import (
    get_width_height_of_image,
)
from sharded_photos_drive_cli_client.shared.gphotos.valid_file_extensions import (
    IMAGE_FILE_EXTENSIONS,
    VIDEO_FILE_EXTENSIONS,
)
from sharded_photos_drive_cli_client.shared.mongodb.album_id import AlbumId
from sharded_photos_drive_cli_client.shared.mongodb.albums_repository import (
    AlbumsRepositoryImpl,
)
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.media_items_repository import (
    FindMediaItemRequest,
    MediaItemsRepositoryImpl,
    UpdateMediaItemRequest,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def set_media_item_width_height_date_taken_fields(
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
        "Called db set-media-item-width-height-date-taken-fields handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
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

    while len(albums_queue) > 0:
        album_id, prev_albums_path = albums_queue.popleft()
        album = albums_repo.get_album_by_id(album_id)

        for child_album_id in album.child_album_ids:
            if album_id == root_album_id:
                albums_queue.append((child_album_id, prev_albums_path + ['.']))
            else:
                albums_queue.append(
                    (child_album_id, prev_albums_path + [cast(str, album.name)])
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

            if (
                media_item.width != 0
                and media_item.height != 0
                and media_item.date_taken != datetime(1970, 1, 1)
            ):
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

            try:
                date_taken = get_date_taken(file_path)
            except Exception as e:
                print(f"get_date_taken() error for {file_path}:")
                print(e)
                continue

            print(f'{file_path}: {width}x{height} from {date_taken}')

            update_media_item_requests.append(
                UpdateMediaItemRequest(
                    media_item_id=media_item.id,
                    new_width=width,
                    new_height=height,
                    new_date_taken=date_taken,
                )
            )

    if prompt_user_for_yes_no_answer('Is this correct? [Y/N]:'):
        media_items_repo.update_many_media_items(update_media_item_requests)
    else:
        print("Operation cancelled")


def get_date_taken(file_path: str) -> datetime:
    with ExifToolHelper() as exiftool_client:
        raw_metadata = exiftool_client.get_tags(
            [file_path],
            [
                "EXIF:DateTimeOriginal",  # for images
                "QuickTime:CreateDate",  # for videos (QuickTime/MP4)
                "QuickTime:CreationDate",
                'RIFF:DateTimeOriginal',  # for avi videos
                'XMP-exif:DateTimeOriginal',  # for gifs
                "TrackCreateDate",
                "MediaCreateDate",
            ],
        )[0]

        date_str = (
            raw_metadata.get("EXIF:DateTimeOriginal")
            or raw_metadata.get("QuickTime:CreateDate")
            or raw_metadata.get('QuickTime:CreationDate')
            or raw_metadata.get('RIFF:DateTimeOriginal')
            or raw_metadata.get('XMP-exif:DateTimeOriginal')
            or raw_metadata.get('TrackCreateDate')
            or raw_metadata.get('MediaCreateDate')
        )
        if date_str:
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        else:
            raise ValueError("Cannot get date_taken")
