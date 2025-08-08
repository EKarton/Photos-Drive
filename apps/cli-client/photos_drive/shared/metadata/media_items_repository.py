from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bson.objectid import ObjectId

from photos_drive.shared.llm.vector_stores.base_vector_store import MediaItemEmbeddingId
from photos_drive.shared.metadata.album_id import AlbumId
from photos_drive.shared.metadata.gps_location import GpsLocation
from photos_drive.shared.metadata.media_item_id import MediaItemId
from photos_drive.shared.metadata.media_items import MediaItem


@dataclass(frozen=True)
class CreateMediaItemRequest:
    """
    A class that represents the parameters needed to create a new media item
    in the database.

    Attributes:
        file_name (str): The file name of the media item.
        file_hash (bytes): The hash of the media item, in bytes.
        location (Optional(GpsLocation)): The location of where the media item was
            taken.
        gphotos_client_id (ObjectId): The ID of the Google Photos client that the media
            item is saved on.
        gphotos_media_item_id (str): The ID of the media item stored on Google Photos.
        album_id (AlbumId): The album that this media item belongs to.
        width (int): The width of the media item.
        height (int): The height of the media item.
        date_taken (datetime): The date and time of when the media item was taken.
        embedding_id (Optional[MediaItemEmbeddingId]): An ID referring to its embedding,
            if present.
    """

    file_name: str
    file_hash: bytes
    location: Optional[GpsLocation]
    gphotos_client_id: ObjectId
    gphotos_media_item_id: str
    album_id: AlbumId
    width: int
    height: int
    date_taken: datetime
    embedding_id: Optional[MediaItemEmbeddingId]


@dataclass(frozen=True)
class UpdateMediaItemRequest:
    '''
    A class that represents the parameters needed to update an existing media item in
    the database.

    Attributes:
        media_item_id (MediaItemId): The ID of the media item to update.
        new_file_name (Optional[str]): The new file name, if present.
        new_file_hash (Optional[bytes]): The new file hash, if present.
        clear_location (Optional[bool]): Whether to clear the gps location or not,
            if present.
        new_location (Optional[GpsLocation | None]): The new gps location,
            if present.
        new_gphotos_client_id (Optional[ObjectId]): The new GPhotos client ID,
            if present.
        new_gphotos_media_item_id (Optional[str]): The new GPhotos media item ID,
            if present.
        new_album_id (Optional[AlbumId]): The new Album ID.
        new_width (Optional[int]): The new width.
        new_height (Optional[int]): The new height.
        new_date_taken (Optional[datetime]): The new date and time of when the
            image / video was taken.
        clear_embedding_id (bool): Whether to clear the embedding ID.
        new_embedding_id (Optional[MediaItemEmbeddingId]): The new embedding ID.
    '''

    media_item_id: MediaItemId
    new_file_name: Optional[str] = None
    new_file_hash: Optional[bytes] = None
    clear_location: Optional[bool] = False
    new_location: Optional[GpsLocation] = None
    new_gphotos_client_id: Optional[ObjectId] = None
    new_gphotos_media_item_id: Optional[str] = None
    new_album_id: Optional[AlbumId] = None
    new_width: Optional[int] = None
    new_height: Optional[int] = None
    new_date_taken: Optional[datetime] = None
    clear_embedding_id: Optional[bool] = False
    new_embedding_id: Optional[MediaItemEmbeddingId] = None


@dataclass(frozen=True)
class LocationRange:
    location: GpsLocation
    radius: float


@dataclass(frozen=True)
class FindMediaItemRequest:
    '''
    A class that represents the parameters needed to find existing media items in
    the database.

    Attributes:
        mongodb_client_ids (Optional[list[ObjectId]): A list of client IDs to search
            through, if present. If not present, it will search through all MongoDB
            clients.
        file_name (Optional[str]): The file name, if present.
        album_id (Optional[AlbumId]): The Album ID, if present.
        earliest_date_taken (Optional[datetime]): The earliest date taken to consider
            in the search, if present.
        latest_date_taken (Optional[datetime]): The latest date taken to consider
            in the search, if present.
        location_range (Optional[LocationRange]): The geolocation of which media items
            need to be within, if present.
        limit (Optional[int]): The max. number of items to fetch, if present.
            If not present, it will return all media items.
    '''

    mongodb_client_ids: Optional[list[ObjectId]] = None
    file_name: Optional[str] = None
    album_id: Optional[AlbumId] = None
    earliest_date_taken: Optional[datetime] = None
    latest_date_taken: Optional[datetime] = None
    location_range: Optional[LocationRange] = None
    limit: Optional[int] = None


class MediaItemsRepository(ABC):
    """
    A class that represents a repository of all of the media items in the database.
    """

    @abstractmethod
    def get_media_item_by_id(self, id: MediaItemId) -> MediaItem:
        """
        Returns the media item by ID.

        Args:
            id (MediaItemId): The media item id

        Returns:
            MediaItem: The media item
        """

    @abstractmethod
    def get_all_media_items(self) -> list[MediaItem]:
        """
        Returns all media items.

        Returns:
            list[MediaItem]: A list of all media items.
        """

    @abstractmethod
    def find_media_items(self, request: FindMediaItemRequest) -> list[MediaItem]:
        '''
        Finds all media items that satisfies the request.

        Args:
            request (FindMediaItemRequest): The request.

        Returns:
            list[MediaItem]: A list of found media items.
        '''

    @abstractmethod
    def get_num_media_items_in_album(self, album_id: AlbumId) -> int:
        '''
        Returns the total number of media items in an album.

        Args:
            album_id (AlbumId): The album ID.

        Returns:
            int: total number of media items in an album.
        '''

    @abstractmethod
    def create_media_item(self, request: CreateMediaItemRequest) -> MediaItem:
        """
        Creates a new media item in the database.

        Args:
            request (CreateMediaItemRequest): The request to create media item.

        Returns:
            MediaItem: The media item.
        """

    @abstractmethod
    def update_many_media_items(self, requests: list[UpdateMediaItemRequest]):
        '''
        Updates many media items in the database.

        Args:
            requests (list[UpdateMediaItemRequest]):
                A list of requests to update many media item.
        '''

    @abstractmethod
    def delete_media_item(self, id: MediaItemId):
        """
        Deletes a media item from the database.

        Args:
            id (MediaItemId): The ID of the media item to delete.

        Raises:
            ValueError: If no media item exists.
        """

    @abstractmethod
    def delete_many_media_items(self, ids: list[MediaItemId]):
        """
        Deletes a list of media items from the database.

        Args:
            ids (list[MediaItemId): The IDs of the media items to delete.

        Raises:
            ValueError: If a media item exists.
        """
