from abc import ABC, abstractmethod
from dataclasses import dataclass
import sys
from typing import Optional

from photos_drive.shared.metadata.album_id import AlbumId
from photos_drive.shared.metadata.media_item_id import MediaItemId
from photos_drive.shared.metadata.media_items import MediaItem


@dataclass(frozen=True)
class GetNumMediaItemsInTileRequest:
    '''
    Represents a request to fetch the number of media items in a tile.

    Attributes:
        x (number): The x portion of a tile
        y (number): The y portion of a tile
        z: (number): The zoom level of a tile
        album_id (Optional[AlbumId]): Whether to focus only on an album or not.
    '''

    x: int
    y: int
    z: int
    album_id: Optional[AlbumId]


@dataclass(frozen=True)
class GetMediaItemsInTileRequest:
    '''
    Represents a request to fetch media items in a tile.

    Attributes:
        x (number): The x portion of a tile
        y (number): The y portion of a tile
        z: (number): The zoom level of a tile
        album_id (Optional[AlbumId]): Whether to focus only on an album or not.
        limit (number): The max number of media items to fetch.
    '''

    x: int
    y: int
    z: int
    album_id: Optional[AlbumId]
    limit: int = sys.maxsize


class TilesRepository(ABC):
    """
    A class that represents a repository of tiles.
    """

    @abstractmethod
    def add_media_item(self, media_item: MediaItem):
        '''
        Adds a media item to the tiles repository.
        '''
        pass

    @abstractmethod
    def remove_media_item(self, media_item: MediaItem):
        '''
        Removes a media item from the tiles repository,
        assuming the media item exists in the tile repository.

        Args:
            media_item (MediaItem): The media item to remove
        '''
        pass

    @abstractmethod
    def get_num_media_items_in_tile(
        self, request: GetNumMediaItemsInTileRequest
    ) -> int:
        '''
        Returns the number of media items that reside in a tile.

        Args:
            request (GetMediaItemsRequest): specs on the tile
        '''
        pass

    @abstractmethod
    def get_media_item_ids_in_tile(
        self, request: GetMediaItemsInTileRequest
    ) -> list[MediaItemId]:
        '''
        Returns the media item ids that reside in a tile.

        Args:
            request (GetMediaItemsRequest): specs on the tile
        '''
        pass
