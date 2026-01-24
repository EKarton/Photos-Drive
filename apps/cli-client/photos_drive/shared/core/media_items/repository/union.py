from collections import defaultdict
from typing import Mapping

from bson.objectid import ObjectId

from photos_drive.shared.core.albums.album_id import AlbumId
from photos_drive.shared.core.media_items.media_item import MediaItem
from photos_drive.shared.core.media_items.media_item_id import MediaItemId
from photos_drive.shared.core.media_items.repository.base import (
    CreateMediaItemRequest,
    FindMediaItemRequest,
    MediaItemsRepository,
    UpdateMediaItemRequest,
)


class UnionMediaItemsRepository(MediaItemsRepository):
    """
    An implementation of MediaItemsRepository that federates multiple repositories.
    """

    def __init__(self, repositories: list[MediaItemsRepository]):
        """
        Creates a UnionMediaItemsRepository.

        Args:
            repositories (list[MediaItemsRepository]): A list of repositories to federate.
        """
        self._repositories = repositories
        self._client_id_to_repo: Mapping[ObjectId, MediaItemsRepository] = {
            repo.get_client_id(): repo for repo in repositories
        }

    def get_client_id(self) -> ObjectId:
        raise NotImplementedError("Union repository does not have a single client ID")

    def get_available_free_space(self) -> int:
        return sum(repo.get_available_free_space() for repo in self._repositories)

    def get_media_item_by_id(self, id: MediaItemId) -> MediaItem:
        if id.client_id not in self._client_id_to_repo:
            raise ValueError(f"No repository found for client {id.client_id}")
        return self._client_id_to_repo[id.client_id].get_media_item_by_id(id)

    def get_all_media_items(self) -> list[MediaItem]:
        all_items = []
        for repo in self._repositories:
            all_items.extend(repo.get_all_media_items())
        return all_items

    def find_media_items(self, request: FindMediaItemRequest) -> list[MediaItem]:
        all_items = []
        for repo in self._repositories:
            all_items.extend(repo.find_media_items(request))
        return all_items

    def get_num_media_items_in_album(self, album_id: AlbumId) -> int:
        # We need to sum across all repositories because an album ID is unique to a client,
        # but the union repo doesn't assume which client the album belongs to here
        # (though usually AlbumId.client_id tells us).
        # Actually, since album_id has client_id, we could optimize:
        if album_id.client_id in self._client_id_to_repo:
            return self._client_id_to_repo[
                album_id.client_id
            ].get_num_media_items_in_album(album_id)

        # Fallback to search all (shouldn't happen if AlbumId is correctly used)
        total = 0
        for repo in self._repositories:
            total += repo.get_num_media_items_in_album(album_id)
        return total

    def create_media_item(self, request: CreateMediaItemRequest) -> MediaItem:
        # Find the repository with the most free space
        target_repo = max(
            self._repositories, key=lambda repo: repo.get_available_free_space()
        )
        return target_repo.create_media_item(request)

    def update_many_media_items(self, requests: list[UpdateMediaItemRequest]):
        requests_by_client = defaultdict(list)
        for request in requests:
            requests_by_client[request.media_item_id.client_id].append(request)

        for client_id, client_requests in requests_by_client.items():
            if client_id not in self._client_id_to_repo:
                raise ValueError(f"No repository found for client {client_id}")
            self._client_id_to_repo[client_id].update_many_media_items(client_requests)

    def delete_media_item(self, id: MediaItemId):
        if id.client_id not in self._client_id_to_repo:
            raise ValueError(f"No repository found for client {id.client_id}")
        self._client_id_to_repo[id.client_id].delete_media_item(id)

    def delete_many_media_items(self, ids: list[MediaItemId]):
        ids_by_client = defaultdict(list)
        for media_item_id in ids:
            ids_by_client[media_item_id.client_id].append(media_item_id)

        for client_id, client_ids in ids_by_client.items():
            if client_id not in self._client_id_to_repo:
                raise ValueError(f"No repository found for client {client_id}")
            self._client_id_to_repo[client_id].delete_many_media_items(client_ids)
