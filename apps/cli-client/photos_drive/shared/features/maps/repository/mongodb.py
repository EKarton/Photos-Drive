import sys
from typing import cast

from bson.objectid import ObjectId
import h3

from photos_drive.shared.core.albums.album_id import album_id_to_string
from photos_drive.shared.core.clients.mongodb import (
    MongoDbClientsRepository,
)
from photos_drive.shared.core.media_items.media_item import MediaItem
from photos_drive.shared.core.media_items.media_item_id import (
    MediaItemId,
    media_item_id_to_string,
)
from photos_drive.shared.features.maps.repository.base import MapCellsRepository

MAX_CELL_RESOLUTION = 15


class MongoDBMapCellsRepository(MapCellsRepository):
    """Implementation class for MapCellsRepository using a single MongoDB client."""

    def __init__(
        self, client_id: ObjectId, mongodb_clients_repository: MongoDbClientsRepository
    ):
        """
        Creates a MongoDBMapCellsRepository

        Args:
            client_id (ObjectId): The ID of the mongo db client that stores the tiles.
            mongodb_clients_repository (MongoDbClientsRepository): A repo of mongo db
                clients.
        """
        self._client_id = client_id
        self._mongodb_clients_repository = mongodb_clients_repository

    def get_client_id(self) -> ObjectId:
        return self._client_id

    def get_available_free_space(self) -> int:
        for (
            client_id,
            free_space,
        ) in self._mongodb_clients_repository.get_free_space_for_all_clients():
            if client_id == self._client_id:
                return free_space
        return -sys.maxsize - 1

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

        client = self._mongodb_clients_repository.get_client_by_id(self._client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )

        docs = [
            {
                "cell_id": cid,
                "album_id": album_id_to_string(media_item.album_id),
                "media_item_id": media_item_id_to_string(media_item.id),
            }
            for cid in cell_ids
        ]

        client["photos_drive"]["map_cells"].insert_many(
            docs,
            session=session,
        )

    def remove_media_item(self, media_item_id: MediaItemId):
        client = self._mongodb_clients_repository.get_client_by_id(self._client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )
        client["photos_drive"]["map_cells"].delete_many(
            filter={
                "media_item_id": media_item_id_to_string(media_item_id),
            },
            session=session,
        )
