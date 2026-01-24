from typing import Mapping

from bson.objectid import ObjectId

from photos_drive.shared.core.databases.mongodb import MongoDBClientsRepository
from photos_drive.shared.core.media_items.media_item import MediaItem
from photos_drive.shared.core.media_items.media_item_id import MediaItemId
from photos_drive.shared.features.maps.repository.base import MapCellsRepository
from photos_drive.shared.features.maps.repository.mongodb import (
    MongoDBMapCellsRepository,
)

MAX_CELL_RESOLUTION = 15


class UnionMapCellsRepository(MapCellsRepository):
    """
    An implementation of MapCellsRepository that federates multiple repositories.
    """

    def __init__(self, repositories: list[MapCellsRepository]):
        """
        Creates a UnionMapCellsRepository.

        Args:
            repositories (list[MapCellsRepository]): A list of repositories to federate.
        """
        self._repositories = repositories
        self._client_id_to_repo: Mapping[ObjectId, MapCellsRepository] = {
            repo.get_client_id(): repo for repo in repositories
        }

    def get_client_id(self) -> ObjectId:
        raise NotImplementedError("Union repository does not have a single client ID")

    def get_available_free_space(self) -> int:
        return sum(repo.get_available_free_space() for repo in self._repositories)

    def add_media_item(self, media_item: MediaItem):
        if not media_item.location:
            raise ValueError(f"No gps location for media item {media_item}")

        target_repo = max(
            self._repositories, key=lambda repo: repo.get_available_free_space()
        )
        target_repo.add_media_item(media_item)

    def remove_media_item(self, media_item_id: MediaItemId):
        for repo in self._repositories:
            repo.remove_media_item(media_item_id)


def create_union_map_cells_repository_from_db_clients(
    mongodb_clients_repo: MongoDBClientsRepository,
) -> UnionMapCellsRepository:
    """
    Creates a UnionMapCellsRepository from a MongoDBClientsRepository.

    Args:
        mongodb_clients_repo (MongoDBClientsRepository): The MongoDB clients repository.

    Returns:
        UnionMapCellsRepository: The UnionMapCellsRepository.
    """
    return UnionMapCellsRepository(
        [
            MongoDBMapCellsRepository(client_id, client, mongodb_clients_repo)
            for (client_id, client) in mongodb_clients_repo.get_all_clients()
        ]
    )
