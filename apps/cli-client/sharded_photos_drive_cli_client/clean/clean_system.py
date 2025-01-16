from dataclasses import dataclass
from typing import Dict
from collections import deque
from bson.objectid import ObjectId
import logging

from ..shared.gphotos.client import GPhotosClientV2
from ..shared.gphotos.albums import Album as GAlbum
from ..shared.mongodb.albums import AlbumId
from ..shared.mongodb.media_items import MediaItemId
from ..shared.gphotos.clients_repository import GPhotosClientsRepository
from ..shared.config.config import Config
from ..shared.mongodb.albums_repository import AlbumsRepository
from ..shared.mongodb.media_items_repository import MediaItemsRepository

logger = logging.getLogger(__name__)


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
    '''
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
    '''

    client_id: ObjectId
    object_id: str


class SystemCleaner:
    def __init__(
        self,
        config: Config,
        albums_repo: AlbumsRepository,
        media_items_repo: MediaItemsRepository,
        gphotos_clients_repo: GPhotosClientsRepository,
    ):
        self.__config = config
        self.__albums_repo = albums_repo
        self.__media_items_repo = media_items_repo
        self.__gphotos_clients_repo = gphotos_clients_repo

    def clean(self) -> CleanupResults:
        mongodb_clients = self.__config.get_mongo_db_clients()
        sessions = [client.start_session() for _, client in mongodb_clients]
        try:
            for session in sessions:
                session.start_transaction()

            cleanup_results = self.__clean_internal()

            for session in sessions:
                session.commit_transaction()
                session.end_session()

            logger.debug("Transaction committed successfully")

            return cleanup_results
        except BaseException as e:
            logger.error("Aborting transaction due to an error:", str(e))
            for session in sessions:
                session.abort_transaction()
                session.end_session()

            logger.error("Aborted transaction")
            raise e

    def __clean_internal(self) -> CleanupResults:
        # Step 1: Find all of the media item ids and all of the album ids to delete
        media_item_ids_to_delete, album_ids_to_delete = (
            self.__find_media_item_ids_and_album_ids_to_delete()
        )

        # Step 2: Find all of the GPhotos media items to move to trash
        gmedia_item_keys_to_trash = self.__find_gmedia_item_keys_to_trash(
            media_item_ids_to_delete
        )

        # Step 3: Delete the media items that were marked to be deleted
        self.__media_items_repo.delete_many_media_items(list(media_item_ids_to_delete))

        # Step 4: Delete the albums that were marked to be deleted
        self.__albums_repo.delete_many_albums(list(album_ids_to_delete))

        # Step 5: Move all the gmedia items marked for trash to a folder called Trash
        self.__move_gmedia_items_to_trash(gmedia_item_keys_to_trash)

        return CleanupResults(
            num_media_items_deleted=len(media_item_ids_to_delete),
            num_albums_deleted=len(album_ids_to_delete),
            num_gmedia_items_moved_to_trash=len(gmedia_item_keys_to_trash),
        )

    def __find_media_item_ids_and_album_ids_to_delete(
        self,
    ) -> tuple[set[MediaItemId], set[AlbumId]]:
        media_item_ids_to_delete = set(
            [item.id for item in self.__media_items_repo.get_all_media_items()]
        )
        album_ids_to_delete = set(
            [item.id for item in self.__albums_repo.get_all_albums()]
        )

        root_album_id = self.__config.get_root_album_id()
        album_ids_to_delete.remove(root_album_id)
        albums_queue = deque([root_album_id])

        while len(albums_queue) > 0:
            cur_album_id = albums_queue.popleft()
            cur_album = self.__albums_repo.get_album_by_id(cur_album_id)

            if cur_album_id in album_ids_to_delete:
                is_empty_leaf_album = (
                    len(cur_album.child_album_ids) == 0
                    and len(cur_album.media_item_ids) == 0
                )
                if not is_empty_leaf_album:
                    album_ids_to_delete.remove(cur_album_id)

            for child_album_id in cur_album.child_album_ids:
                albums_queue.append(child_album_id)

            for media_item_id in cur_album.media_item_ids:
                if media_item_id in media_item_ids_to_delete:
                    media_item_ids_to_delete.remove(media_item_id)

        return media_item_ids_to_delete, album_ids_to_delete

    def __find_gmedia_item_keys_to_trash(
        self, media_item_ids_to_delete: set[MediaItemId]
    ) -> set[GPhotosMediaItemKey]:
        gmedia_item_ids_to_trash = set([])
        gphotos_clients = self.__gphotos_clients_repo.get_all_clients()
        for gphotos_client_id, gphotos_client in gphotos_clients:
            for gmedia_item in gphotos_client.media_items().search_for_media_items():
                gmedia_item_key = GPhotosMediaItemKey(
                    client_id=gphotos_client_id, object_id=gmedia_item.id
                )
                gmedia_item_ids_to_trash.add(gmedia_item_key)

        for media_item_id in media_item_ids_to_delete:
            media_item = self.__media_items_repo.get_media_item_by_id(media_item_id)
            gmedia_item_key = GPhotosMediaItemKey(
                client_id=media_item.gphotos_client_id,
                object_id=media_item.gphotos_media_item_id,
            )

            if gmedia_item_key in gmedia_item_ids_to_trash:
                gmedia_item_ids_to_trash.remove(gmedia_item_key)

        return gmedia_item_ids_to_trash

    def __move_gmedia_items_to_trash(self, gmedia_item_keys: list[GPhotosMediaItemKey]):
        client_id_to_gmedia_item_ids: Dict[ObjectId, list[str]] = {}

        for key in gmedia_item_keys:

            if key.client_id not in client_id_to_gmedia_item_ids:
                client_id_to_gmedia_item_ids[key.client_id] = []

            client_id_to_gmedia_item_ids[key.client_id].append(key.object_id)

        for client_id in client_id_to_gmedia_item_ids:
            client = self.__gphotos_clients_repo.get_client_by_id(client_id)
            trash_album = self.__find_or_create_trash_album(client)

            self.__move_gmedia_item_ids_to_album_safely(
                client, trash_album.id, client_id_to_gmedia_item_ids[client_id]
            )

    def __find_or_create_trash_album(self, client: GPhotosClientV2) -> GAlbum:
        trash_album: GAlbum | None = None
        for album in client.albums().list_albums(exclude_non_app_created_data=True):
            if album.title == 'To delete':
                trash_album = album
                break

        if not trash_album:
            trash_album = client.albums().create_album("To delete")

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
