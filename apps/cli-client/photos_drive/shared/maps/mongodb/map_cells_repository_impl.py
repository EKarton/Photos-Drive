import sys
from typing import Dict, cast

from bson.objectid import ObjectId
import h3

from photos_drive.shared.maps.map_cells_repository import MapCellsRepository
from photos_drive.shared.metadata.album_id import album_id_to_string
from photos_drive.shared.metadata.media_item_id import (
    MediaItemId,
    media_item_id_to_string,
)
from photos_drive.shared.metadata.media_items import MediaItem
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)

MAX_CELL_RESOLUTION = 15


class MapCellsRepositoryImpl(MapCellsRepository):
    """Implementation class for MapCellsRepository."""

    def __init__(self, mongodb_clients_repository: MongoDbClientsRepository):
        """
        Creates a CellsRepositoryImpl

        Args:
            mongodb_clients_repository (MongoDbClientsRepository): A repo of mongo db
                clients that stores the tiles.
        """
        self.mongodb_clients_repository = mongodb_clients_repository

    def add_media_item(self, media_item: MediaItem):
        if not media_item.location:
            raise ValueError(f"No gps location for media item {media_item}")

        cell_id = h3.latlng_to_cell(
            media_item.location.latitude,
            media_item.location.longitude,
            MAX_CELL_RESOLUTION,
        )
        cell_ids = set(
            cast(str, h3.cell_to_parent(cell_id, res))
            for res in range(0, MAX_CELL_RESOLUTION + 1)
        )

        client_id_to_cell_ids: Dict[ObjectId, set[str]] = {}
        free_spaces = self.mongodb_clients_repository.get_free_space_for_all_clients()
        for cell_id in cell_ids:
            best_free_space = -sys.maxsize - 1
            best_client_id = None
            best_idx = None

            for i in range(len(free_spaces)):
                client_id, free_space = free_spaces[i]
                if free_space <= 0:
                    continue

                if free_space > best_free_space:
                    best_free_space = free_space
                    best_client_id = client_id
                    best_idx = i

            if best_client_id is None or best_idx is None:
                raise ValueError("Unable to find space to insert h3 map cells")

            if best_client_id not in client_id_to_cell_ids:
                client_id_to_cell_ids[best_client_id] = set()
            client_id_to_cell_ids[best_client_id].add(cell_id)

            # Decrement the free space for the chosen client
            free_spaces[best_idx] = (best_client_id, best_free_space - 1)

        for client_id, client_id_cell_ids in client_id_to_cell_ids.items():
            client_id = (
                self.mongodb_clients_repository.find_id_of_client_with_most_space()
            )
            client = self.mongodb_clients_repository.get_client_by_id(client_id)
            session = self.mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )

            docs = [
                {
                    "cell_id": cell_id,
                    "album_id": album_id_to_string(media_item.album_id),
                    "media_item_id": media_item_id_to_string(media_item.id),
                }
                for cell_id in client_id_cell_ids
            ]

            client["photos_drive"]["map_cells"].insert_many(
                docs,
                session=session,
            )

    def remove_media_item(self, media_item_id: MediaItemId):
        for client_id, client in self.mongodb_clients_repository.get_all_clients():
            session = self.mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            client['photos_drive']['map_cells'].delete_many(
                filter={
                    "media_item_id": media_item_id_to_string(media_item_id),
                },
                session=session,
            )
