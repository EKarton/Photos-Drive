from dataclasses import dataclass
from typing import Dict, Optional
from bson.objectid import ObjectId
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed, wait

from ..shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
    MongoDbTransactionsContext,
)
from ..shared.mongodb.albums_pruner import AlbumsPruner
from ..shared.gphotos.client import GPhotosClientV2
from ..shared.mongodb.albums import AlbumId
from ..shared.mongodb.media_items import MediaItemId
from ..shared.gphotos.clients_repository import GPhotosClientsRepository
from ..shared.config.config import Config
from ..shared.mongodb.albums_repository import AlbumsRepository, UpdatedAlbumFields
from ..shared.mongodb.media_items_repository import MediaItemsRepository

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
        # Step 1: Delete all albums in GPhotos
        self.__delete_all_albums()

        # Step 2: Find all albums
        all_album_ids = self.__find_all_albums()

        # Step 3: Find all media items
        all_media_item_ids = self.__find_all_media_items()

        # Step 4: Find all gphoto media items
        all_gphoto_media_item_ids = self.__find_all_gmedia_items()

        # Step 5: Find all the content that we want to keep
        album_ids_to_keep, media_item_ids_to_keep, gmedia_item_ids_to_keep = (
            self.__find_content_to_keep(
                all_album_ids, all_media_item_ids, all_gphoto_media_item_ids
            )
        )

        # Step 6: Delete all unlinked albums
        album_ids_to_delete = all_album_ids - album_ids_to_keep
        self.__albums_repo.delete_many_albums(list(album_ids_to_delete))

        # Step 7: Delete all unlinked media items
        media_item_ids_to_delete = all_media_item_ids - media_item_ids_to_keep
        self.__media_items_repo.delete_many_media_items(list(media_item_ids_to_delete))

        # Step 8: Delete all unlinked gphoto media items
        gphoto_media_item_ids_to_delete = (
            all_gphoto_media_item_ids - gmedia_item_ids_to_keep
        )
        self.__move_gmedia_items_to_trash(list(gphoto_media_item_ids_to_delete))

        # Step 9: Prune all the leaf albums in the tree
        num_albums_pruned = self.__prune_albums()

        return CleanupResults(
            num_media_items_deleted=len(media_item_ids_to_delete),
            num_albums_deleted=len(album_ids_to_delete) + num_albums_pruned,
            num_gmedia_items_moved_to_trash=len(gphoto_media_item_ids_to_delete),
        )

    def __delete_all_albums(self):
        logger.info("Deleting all albums in Google Photos")
        albums_to_delete: list[tuple[str, str]] = []

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(client.albums().list_albums, True): client_id
                for client_id, client in self.__gphotos_clients_repo.get_all_clients()
            }

            for future in as_completed(futures):
                albums = future.result()
                client_id = futures[future]
                albums_to_delete += [(client_id, album.id) for album in albums]

        with ThreadPoolExecutor() as executor:
            futures = []

            for client_id, album_id in albums_to_delete:
                client = self.__gphotos_clients_repo.get_client_by_id(client_id)
                futures.append(executor.submit(client.albums().delete_album, album_id))

            wait(futures)

        logger.info("Deleted all albums in Google Photos")

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
        gmedia_item_ids = []
        with ThreadPoolExecutor() as executor:
            futures = {}

            for client_id, client in self.__gphotos_clients_repo.get_all_clients():
                future = executor.submit(client.media_items().search_for_media_items)
                futures[future] = client_id

            for future in as_completed(futures):
                raw_gmedia_items = future.result()
                client_id = futures[future]
                gmedia_item_ids += [
                    GPhotosMediaItemKey(client_id, raw_gmedia_item.id)
                    for raw_gmedia_item in raw_gmedia_items
                ]

        logger.info("Finished finding all gmedia items")
        return set(gmedia_item_ids)

    def __find_content_to_keep(
        self,
        all_album_ids: set[AlbumId],
        all_media_item_ids: set[MediaItemId],
        all_gphoto_media_item_ids: set[GPhotosMediaItemKey],
    ) -> tuple[set[AlbumId], set[MediaItemId], set[GPhotosMediaItemKey]]:
        album_ids_to_keep: list[AlbumId] = []
        media_item_ids_to_keep: list[MediaItemId] = []
        gmedia_item_ids_to_keep: list[GPhotosMediaItemKey] = []

        queue = deque([self.__config.get_root_album_id()])
        while len(queue) > 0:
            album_id = queue.popleft()
            album = self.__albums_repo.get_album_by_id(album_id)
            album_ids_to_keep.append(album_id)

            sub_media_item_ids_to_keep = []
            sub_media_item_ids_to_keep_changed = False
            for media_item_id in album.media_item_ids:
                if media_item_id not in all_media_item_ids:
                    sub_media_item_ids_to_keep_changed = True
                    continue

                media_item = self.__media_items_repo.get_media_item_by_id(media_item_id)
                gphotos_media_item_id = GPhotosMediaItemKey(
                    media_item.gphotos_client_id,
                    media_item.gphotos_media_item_id,
                )

                if gphotos_media_item_id not in all_gphoto_media_item_ids:
                    sub_media_item_ids_to_keep_changed = True
                    continue

                sub_media_item_ids_to_keep.append(media_item_id)
                media_item_ids_to_keep.append(media_item_id)
                gmedia_item_ids_to_keep.append(gphotos_media_item_id)

            sub_child_album_ids_to_keep = []
            sub_child_album_ids_to_keep_changed = False
            for child_album_id in album.child_album_ids:
                if child_album_id not in all_album_ids:
                    sub_child_album_ids_to_keep_changed = True
                    continue

                sub_child_album_ids_to_keep.append(child_album_id)

            if (
                sub_media_item_ids_to_keep_changed
                or sub_child_album_ids_to_keep_changed
            ):
                self.__albums_repo.update_album(
                    album_id,
                    UpdatedAlbumFields(
                        new_media_item_ids=(
                            sub_media_item_ids_to_keep
                            if sub_media_item_ids_to_keep_changed
                            else None
                        ),
                        new_child_album_ids=(
                            sub_child_album_ids_to_keep
                            if sub_child_album_ids_to_keep_changed
                            else None
                        ),
                    ),
                )

            for child_album_id in sub_child_album_ids_to_keep:
                queue.append(child_album_id)

        return (
            set(album_ids_to_keep),
            set(media_item_ids_to_keep),
            set(gmedia_item_ids_to_keep),
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
            trash_album = client.albums().create_album(TRASH_ALBUM_TITLE)

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
            prune_album_id = (
                album_id
                if len(child_album_ids) == 0 and len(album.media_item_ids) == 0
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
        pruner = AlbumsPruner(root_album_id, self.__albums_repo)
        for album_id in empty_leaf_album_ids:
            with MongoDbTransactionsContext(self.__mongodb_clients_repo):
                total_albums_pruned += pruner.prune_album(album_id)

        logger.info("Finished pruning albums")
        return total_albums_pruned
