from typing import cast

from bson.objectid import ObjectId
import h3

from pymongo import MongoClient

from photos_drive.shared.utils.mongodb.get_free_space import get_free_space
from photos_drive.shared.core.albums.album_id import album_id_to_string
from photos_drive.shared.core.database.mongodb import (
    MongoDbTransactionRepository,
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
        self,
        client_id: ObjectId,
        mongodb_client: MongoClient,
        mongodb_transactions_repository: MongoDbTransactionRepository,
    ):
        """
        Creates a MongoDBMapCellsRepository

        Args:
            client_id (ObjectId): The ID of the mongo db client that stores the tiles.
            mongodb_client (MongoClient): The MongoDB client.
            mongodb_transactions_repository (MongoDbTransactionRepository):
                A repo of mongo db clients.
        """
        self._client_id = client_id
        self._mongodb_transactions_repository = mongodb_transactions_repository
        self._mongodb_client = mongodb_client

    def get_client_id(self) -> ObjectId:
        return self._client_id

    def get_available_free_space(self) -> int:
        return get_free_space(self._mongodb_client)

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

        session = self._mongodb_transactions_repository.get_session_for_client_id(
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

        self._mongodb_client["photos_drive"]["map_cells"].insert_many(
            docs,
            session=session,
        )

    def remove_media_item(self, media_item_id: MediaItemId):
        session = self._mongodb_transactions_repository.get_session_for_client_id(
            self._client_id,
        )
        self._mongodb_client["photos_drive"]["map_cells"].delete_many(
            filter={
                "media_item_id": media_item_id_to_string(media_item_id),
            },
            session=session,
        )
