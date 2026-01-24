from collections import defaultdict
from typing import Mapping

from bson.objectid import ObjectId

from photos_drive.shared.core.albums.album_id import AlbumId
from photos_drive.shared.core.albums.albums import Album
from photos_drive.shared.core.albums.repository.base import (
    AlbumsRepository,
    UpdateAlbumRequest,
    UpdatedAlbumFields,
)


class UnionAlbumsRepository(AlbumsRepository):
    """
    An implementation of AlbumsRepository that federates multiple repositories.
    """

    def __init__(self, repositories: list[AlbumsRepository]):
        """
        Creates a UnionAlbumsRepository.

        Args:
            repositories (list[AlbumsRepository]): A list of repositories to federate.
        """
        self._repositories = repositories
        self._client_id_to_repo: Mapping[ObjectId, AlbumsRepository] = {
            repo.get_client_id(): repo for repo in repositories
        }

    def get_client_id(self) -> ObjectId:
        raise NotImplementedError("Union repository does not have a single client ID")

    def get_available_free_space(self) -> int:
        return sum(repo.get_available_free_space() for repo in self._repositories)

    def get_album_by_id(self, id: AlbumId) -> Album:
        if id.client_id not in self._client_id_to_repo:
            raise ValueError(f"No repository found for client {id.client_id}")
        return self._client_id_to_repo[id.client_id].get_album_by_id(id)

    def get_all_albums(self) -> list[Album]:
        all_albums = []
        for repo in self._repositories:
            all_albums.extend(repo.get_all_albums())
        return all_albums

    def create_album(
        self,
        album_name: str,
        parent_album_id: AlbumId | None,
    ) -> Album:
        # Find the repository with the most free space
        # Note: This simple strategy mirrors the original MongoDB implementation
        # of delegating to the client with the most space.
        target_repo = max(
            self._repositories, key=lambda repo: repo.get_available_free_space()
        )
        return target_repo.create_album(album_name, parent_album_id)

    def delete_album(self, id: AlbumId):
        if id.client_id not in self._client_id_to_repo:
            raise ValueError(f"No repository found for client {id.client_id}")
        self._client_id_to_repo[id.client_id].delete_album(id)

    def delete_many_albums(self, ids: list[AlbumId]):
        ids_by_client = defaultdict(list)
        for album_id in ids:
            ids_by_client[album_id.client_id].append(album_id)

        for client_id, client_ids in ids_by_client.items():
            if client_id not in self._client_id_to_repo:
                raise ValueError(f"No repository found for client {client_id}")
            self._client_id_to_repo[client_id].delete_many_albums(client_ids)

    def update_album(self, album_id: AlbumId, updated_album_fields: UpdatedAlbumFields):
        if album_id.client_id not in self._client_id_to_repo:
            raise ValueError(f"No repository found for client {album_id.client_id}")
        self._client_id_to_repo[album_id.client_id].update_album(
            album_id, updated_album_fields
        )

    def update_many_albums(self, requests: list[UpdateAlbumRequest]):
        requests_by_client = defaultdict(list)
        for request in requests:
            requests_by_client[request.album_id.client_id].append(request)

        for client_id, client_requests in requests_by_client.items():
            if client_id not in self._client_id_to_repo:
                raise ValueError(f"No repository found for client {client_id}")
            self._client_id_to_repo[client_id].update_many_albums(client_requests)

    def find_child_albums(self, album_id: AlbumId) -> list[Album]:
        child_albums = []
        for repo in self._repositories:
            child_albums.extend(repo.find_child_albums(album_id))
        return child_albums

    def count_child_albums(self, album_id: AlbumId) -> int:
        total = 0
        for repo in self._repositories:
            total += repo.count_child_albums(album_id)
        return total
