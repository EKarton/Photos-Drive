from dataclasses import dataclass
from typing import Dict, Optional
from bson.objectid import ObjectId
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, wait

from ..shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
    MongoDbTransactionsContext,
)
from ..shared.mongodb.albums_pruner import AlbumsPruner
from ..shared.gphotos.albums import Album as GAlbum
from ..shared.gphotos.client import GPhotosClientV2
from ..shared.mongodb.album_id import AlbumId
from ..shared.mongodb.media_item_id import MediaItemId
from ..shared.gphotos.clients_repository import GPhotosClientsRepository
from ..shared.config.config import Config
from ..shared.mongodb.albums_repository import AlbumsRepository, UpdatedAlbumFields
from ..shared.mongodb.media_items_repository import (
    FindMediaItemRequest,
    MediaItemsRepository,
)

logger = logging.getLogger(__name__)

TRASH_ALBUM_TITLE = 'To delete'


@dataclass(frozen=True)
class CleanupResults:
    """
    Stores the results of the cleanup.

    Attributes:
        num_media_items_deleted (int): The number of media items deleted.
        num_albums_deleted (int): The number of albums deleted.
        num_gmedia_items_moved_to_trash (int): The number of Google media items moved
            to trash
    """

    num_media_items_deleted: int
    num_albums_deleted: int
    num_gmedia_items_moved_to_trash: int


@dataclass(frozen=True)
class GPhotosMediaItemKey:
    """
    Represents the key of a media item in Google Photos.
    Since Google Photos media items are distributed across different Google Photo
    accounts, it consists of the Google Photos Account client ID and the Google Photos
    media item ID.

    Attributes:
        client_id (ObjectId): The ID of the Google Photos account that it is saved
            under.
        object_id (str): The object ID of the media item in Google Photos
    """

    client_id: ObjectId
    object_id: str


class SystemCleaner:
    def __init__(
        self,
        config: Config,
        albums_repo: AlbumsRepository,
        media_items_repo: MediaItemsRepository,
        gphotos_clients_repo: GPhotosClientsRepository,
        mongodb_clients_repo: MongoDbClientsRepository,
    ):
        self.__config = config
        self.__albums_repo = albums_repo
        self.__media_items_repo = media_items_repo
        self.__gphotos_clients_repo = gphotos_clients_repo
        self.__mongodb_clients_repo = mongodb_clients_repo

    def clean(self) -> CleanupResults:
        # Step 1: Find all albums
        all_album_ids = self.__find_all_albums()
        logger.info(f'Found {len(all_album_ids)} albums')

        # Step 2: Find all media items
        all_media_item_ids = self.__find_all_media_items()
        logger.info(f'Found {len(all_media_item_ids)} media items')

        # Step 3: Find all gphoto media items
        all_gphoto_media_item_ids = self.__find_all_gmedia_items()
        logger.info(f'Found {len(all_gphoto_media_item_ids)} gmedia items')

        # Step 4: Find all the content that we want to keep
        album_ids_to_keep, media_item_ids_to_keep, gmedia_item_ids_to_keep = (
            self.__find_content_to_keep(
                all_album_ids, all_media_item_ids, all_gphoto_media_item_ids
            )
        )
        logger.info(
            f'Keeping {len(album_ids_to_keep)} albums, '
            + f'{len(media_item_ids_to_keep)} media items, and '
            + f'{len(gmedia_item_ids_to_keep)} gmedia items'
        )

        # Step 5: Delete all unlinked albums
        album_ids_to_delete = all_album_ids - album_ids_to_keep
        logger.info(f'Deleting {len(album_ids_to_delete)} albums.')
        self.__albums_repo.delete_many_albums(list(album_ids_to_delete))

        # Step 6: Delete all unlinked media items
        media_item_ids_to_delete = all_media_item_ids - media_item_ids_to_keep
        logger.info(f'Deleting {len(media_item_ids_to_delete)} media items.')
        self.__media_items_repo.delete_many_media_items(list(media_item_ids_to_delete))

        # Step 7: Delete all unlinked gphoto media items
        gphoto_media_item_ids_to_delete = (
            all_gphoto_media_item_ids - gmedia_item_ids_to_keep
        )
        logger.info(f'Trashing {len(gphoto_media_item_ids_to_delete)} photos')
        self.__move_gmedia_items_to_trash(list(gphoto_media_item_ids_to_delete))

        # Step 8: Prune all the leaf albums in the tree
        num_albums_pruned = self.__prune_albums()

        return CleanupResults(
            num_media_items_deleted=len(media_item_ids_to_delete),
            num_albums_deleted=len(album_ids_to_delete) + num_albums_pruned,
            num_gmedia_items_moved_to_trash=len(gphoto_media_item_ids_to_delete),
        )

    def __find_all_albums(self) -> set[AlbumId]:
        logger.info("Finding all albums")
        album_ids = [item.id for item in self.__albums_repo.get_all_albums()]

        logger.info("Finished finding all albums")
        return set(album_ids)

    def __find_all_media_items(self) -> set[MediaItemId]:
        logger.info("Finding all media items")
        media_item_ids = [
            item.id for item in self.__media_items_repo.get_all_media_items()
        ]

        logger.info("Finished finding all media items")
        return set(media_item_ids)

    def __find_all_gmedia_items(self) -> set[GPhotosMediaItemKey]:
        logger.info("Finding all gmedia items")

        def fetch_media_items(client_id, client):
            """Fetch media items for a given client."""
            raw_gmedia_items = client.media_items().get_all_media_items()
            return [
                GPhotosMediaItemKey(client_id, raw_gmedia_item.id)
                for raw_gmedia_item in raw_gmedia_items
            ]

        clients = list(self.__gphotos_clients_repo.get_all_clients())

        # Use ThreadPoolExecutor to parallelize media item fetching
        gmedia_item_ids = []
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(fetch_media_items, client_id, client)
                for client_id, client in clients
            ]

            # Collect results in a thread-safe manner
            results = [future.result() for future in as_completed(futures)]

            # Flatten the results (safe since `results` is local)
            gmedia_item_ids = [item for sublist in results for item in sublist]

        logger.info("Finished finding all gmedia items")

        return set(gmedia_item_ids)

    def __find_content_to_keep(
        self,
        all_album_ids: set[AlbumId],
        all_media_item_ids: set[MediaItemId],
        all_gphoto_media_item_ids: set[GPhotosMediaItemKey],
    ) -> tuple[set[AlbumId], set[MediaItemId], set[GPhotosMediaItemKey]]:
        logger.info(
            "Finding all album ids, media item ids, and gphoto media item ids to keep"
        )

        all_album_ids_to_keep: list[AlbumId] = []
        all_media_ids_to_keep: list[MediaItemId] = []
        all_gmedia_ids_to_keep: list[GPhotosMediaItemKey] = []

        def process_album(
            album_id: AlbumId,
        ) -> tuple[list[MediaItemId], list[GPhotosMediaItemKey], list[AlbumId]]:
            album = self.__albums_repo.get_album_by_id(album_id)
            logger.debug(f'Processing {album.id}')

            # Process media items
            media_ids_to_keep: list[MediaItemId] = []
            gmedia_ids_to_keep: list[GPhotosMediaItemKey] = []

            for media_item in self.__media_items_repo.find_media_items(
                FindMediaItemRequest(album_id=album_id)
            ):
                if media_item.id not in all_media_item_ids:
                    logger.debug(
                        f'Removing gemdia item {media_item.id} from {album.id}'
                    )
                    continue

                gphotos_media_item_id = GPhotosMediaItemKey(
                    media_item.gphotos_client_id,
                    media_item.gphotos_media_item_id,
                )

                if gphotos_media_item_id not in all_gphoto_media_item_ids:
                    logger.debug(
                        f'Removing gemdia item {gphotos_media_item_id} from {album.id}'
                    )
                    continue

                media_ids_to_keep.append(media_item.id)
                gmedia_ids_to_keep.append(gphotos_media_item_id)

            # Process child albums
            child_album_ids_to_keep: list[AlbumId] = []
            child_album_ids_to_keep_changed = False
            for child_album_id in album.child_album_ids:
                if child_album_id not in all_album_ids:
                    logger.debug(
                        f'Removing child album id {child_album_id} from {album.id}'
                    )
                    child_album_ids_to_keep_changed = True
                    continue

                child_album_ids_to_keep.append(child_album_id)

            # Update the album if any changes were detected.
            if child_album_ids_to_keep_changed:
                logger.debug(f'Modifying {album.id}')
                logger.debug(media_ids_to_keep)
                logger.debug(child_album_ids_to_keep)

                self.__albums_repo.update_album(
                    album_id,
                    UpdatedAlbumFields(
                        new_child_album_ids=(
                            child_album_ids_to_keep
                            if child_album_ids_to_keep_changed
                            else None
                        ),
                    ),
                )
            # Return data for merging and the next BFS frontier.
            return (
                media_ids_to_keep,
                gmedia_ids_to_keep,
                child_album_ids_to_keep,
            )

        with ThreadPoolExecutor() as executor:
            cur_level = [self.__config.get_root_album_id()]
            while len(cur_level) > 0:
                # Submit all albums at the current level.
                futures = {
                    executor.submit(process_album, album_id): album_id
                    for album_id in cur_level
                }

                new_level = []
                for future in as_completed(futures):
                    local_media_ids, local_gmedia_ids, child_album_ids = future.result()
                    album_id = futures[future]

                    all_album_ids_to_keep.append(album_id)
                    all_media_ids_to_keep += local_media_ids
                    all_gmedia_ids_to_keep += local_gmedia_ids
                    new_level += child_album_ids

                cur_level = new_level

        logger.info(
            "Finished finding all album ids, media item ids, and gphoto media item ids "
            + "to keep"
        )
        return (
            set(all_album_ids_to_keep),
            set(all_media_ids_to_keep),
            set(all_gmedia_ids_to_keep),
        )

    def __move_gmedia_items_to_trash(self, gmedia_item_keys: list[GPhotosMediaItemKey]):
        logger.info("Moving deleted GPhoto media items to trash album")

        client_id_to_gmedia_item_ids: Dict[ObjectId, list[GPhotosMediaItemKey]] = {}
        for key in gmedia_item_keys:
            if key.client_id not in client_id_to_gmedia_item_ids:
                client_id_to_gmedia_item_ids[key.client_id] = []

            client_id_to_gmedia_item_ids[key.client_id].append(key)

        def process_client(
            client_id: ObjectId,
            gmedia_item_ids: list[GPhotosMediaItemKey],
        ):
            client = self.__gphotos_clients_repo.get_client_by_id(client_id)
            trash_album = self.__find_or_create_trash_album(client)

            self.__move_gmedia_item_ids_to_album_safely(
                client,
                trash_album.id,
                [media_item_id.object_id for media_item_id in gmedia_item_ids],
            )

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    process_client, client_id, client_id_to_gmedia_item_ids[client_id]
                )
                for client_id in client_id_to_gmedia_item_ids
            ]
            wait(futures)

        logger.info("Finished moving deleted GPhoto media items to trash album")

    def __find_or_create_trash_album(self, client: GPhotosClientV2) -> GAlbum:
        trash_album: GAlbum | None = None
        for album in client.albums().list_albums():
            if album.title == TRASH_ALBUM_TITLE:
                trash_album = album
                break

        if not trash_album:
            trash_album = client.albums().create_album(TRASH_ALBUM_TITLE)

        return trash_album

    def __move_gmedia_item_ids_to_album_safely(
        self, client: GPhotosClientV2, galbum_id: str, gmedia_item_ids: list[str]
    ):
        MAX_UPLOAD_TOKEN_LENGTH_PER_CALL = 50

        for i in range(0, len(gmedia_item_ids), MAX_UPLOAD_TOKEN_LENGTH_PER_CALL):
            chunked_gmedia_item_ids = gmedia_item_ids[
                i : i + MAX_UPLOAD_TOKEN_LENGTH_PER_CALL
            ]
            client.albums().add_photos_to_album(galbum_id, chunked_gmedia_item_ids)

    def __prune_albums(self) -> int:
        def process_album(album_id: AlbumId) -> tuple[list[AlbumId], Optional[AlbumId]]:
            album = self.__albums_repo.get_album_by_id(album_id)
            child_album_ids = album.child_album_ids
            num_media_item_ids = self.__media_items_repo.get_num_media_items_in_album(
                album_id
            )
            prune_album_id = (
                album_id
                if len(child_album_ids) == 0 and num_media_item_ids == 0
                else None
            )

            return child_album_ids, prune_album_id

        logger.info("Pruning albums")
        empty_leaf_album_ids = []
        root_album_id = self.__config.get_root_album_id()

        with ThreadPoolExecutor() as executor:
            current_level = [root_album_id]
            while current_level:
                futures = [
                    executor.submit(process_album, album_id)
                    for album_id in current_level
                ]
                next_level = []
                for future in as_completed(futures):
                    children, prune_id = future.result()
                    next_level += children

                    if prune_id is not None:
                        empty_leaf_album_ids.append(prune_id)

                current_level = next_level

        total_albums_pruned = 0
        pruner = AlbumsPruner(
            root_album_id, self.__albums_repo, self.__media_items_repo
        )
        for album_id in empty_leaf_album_ids:
            with MongoDbTransactionsContext(self.__mongodb_clients_repo):
                total_albums_pruned += pruner.prune_album(album_id)

        logger.info("Finished pruning albums")
        return total_albums_pruned
