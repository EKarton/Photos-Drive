from dataclasses import dataclass
from typing import Mapping
import mercantile

from photos_drive.shared.metadata.album_id import AlbumId, album_id_to_string
from photos_drive.shared.metadata.media_item_id import (
    MediaItemId,
    media_item_id_to_string,
    parse_string_to_media_item_id,
)
from photos_drive.shared.metadata.media_items import MediaItem
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.tiles.tiles_repository import (
    GetMediaItemsInTileRequest,
    GetNumMediaItemsInTileRequest,
    TilesRepository,
)

MAX_ZOOM_LEVEL = 15


@dataclass(frozen=True)
class MediaItemTile:
    """
    Represents a tile for a media item in the db. Imagine a map of photos for an album
    (album_id) at a zoom level (z) broken down into tiles. Each tile can be identified
    by (x, y).

    Each tile contains a single media item ID that best represents that tile.
    Each tile also contains the number of media items located in that tile.

    Attributes:
        x (number): The x partition of a tile.
        y (number): The y partition of a tile.
        z (number): The z partition of a tile.
        album_id (AlbumId): The album ID of a tile.
        media_item_id (MediaItemId): The media item ID.
    """

    x: int
    y: int
    z: int
    album_id: AlbumId
    media_item_id: MediaItemId


class TilesRepositoryImpl(TilesRepository):
    """Implementation class for TilesRepository."""

    def __init__(self, mongodb_clients_repository: MongoDbClientsRepository):
        """
        Creates a TilesRepositoryImpl

        Args:
            mongodb_clients_repository (MongoDbClientsRepository): A repo of mongo db
                clients that stores the tiles.
        """
        self.mongodb_clients_repository = mongodb_clients_repository

    def add_media_item(self, media_item: MediaItem):
        if not media_item.location:
            raise ValueError(f"No gps location for media item {media_item}")

        tiles = set(
            [
                mercantile.tile(
                    media_item.location.longitude,
                    media_item.location.latitude,
                    zoom_level,
                )
                for zoom_level in range(0, MAX_ZOOM_LEVEL + 1)
            ]
        )

        for tile in tiles:
            client_id = (
                self.mongodb_clients_repository.find_id_of_client_with_most_space()
            )
            client = self.mongodb_clients_repository.get_client_by_id(client_id)
            session = self.mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            client["photos_drive"]["tiles"].insert_one(
                document={
                    "x": tile.x,
                    "y": tile.y,
                    "z": tile.z,
                    "album_id": album_id_to_string(media_item.album_id),
                    "media_item_id": media_item_id_to_string(media_item.id),
                },
                session=session,
            )

    def remove_media_item(self, media_item: MediaItem):
        if not media_item.location:
            raise ValueError(f"No gps location for media item {media_item}")

        for client_id, client in self.mongodb_clients_repository.get_all_clients():
            session = self.mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            client['photos_drive']['tiles'].delete_many(
                filter={
                    "media_item_id": media_item_id_to_string(media_item.id),
                },
                session=session,
            )

    def get_num_media_items_in_tile(
        self, request: GetNumMediaItemsInTileRequest
    ) -> int:
        filter_obj: Mapping = {
            "x": request.x,
            "y": request.y,
            "z": request.z,
            "album_id": (
                album_id_to_string(request.album_id)
                if request.album_id is not None
                else None
            ),
        }

        total = 0
        for client_id, client in self.mongodb_clients_repository.get_all_clients():
            session = self.mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            total += client['photos_drive']['tiles'].count_documents(
                filter=filter_obj,
                session=session,
            )

        return total

    def get_media_item_ids_in_tile(
        self, request: GetMediaItemsInTileRequest
    ) -> list[MediaItemId]:
        filter_obj: Mapping = {
            "x": request.x,
            "y": request.y,
            "z": request.z,
            "album_id": (
                album_id_to_string(request.album_id)
                if request.album_id is not None
                else None
            ),
        }

        media_item_ids = []
        for client_id, client in self.mongodb_clients_repository.get_all_clients():
            session = self.mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            cursor = (
                client['photos_drive']['tiles']
                .find(
                    filter=filter_obj,
                    session=session,
                )
                .limit(request.limit)
            )

            for doc in cursor:
                media_item_ids.append(
                    parse_string_to_media_item_id(doc['media_item_id'])
                )
                if len(media_item_ids) >= request.limit:
                    break

            if len(media_item_ids) >= request.limit:
                break

        return media_item_ids
