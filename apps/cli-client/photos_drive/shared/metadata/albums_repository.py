from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import Optional

from photos_drive.shared.metadata.album_id import AlbumId
from photos_drive.shared.metadata.albums import Album

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdatedAlbumFields:
    new_name: Optional[str] = None
    new_parent_album_id: Optional[AlbumId] = None


@dataclass(frozen=True)
class UpdateAlbumRequest:
    """
    Represents a request to update an existing album.

    Attributes:
        album_id (AlbumId): The ID of the album.
        new_name (Optional[str]): The new name of the album,
            if present.
        new_parent_album_id (Optional[AlbumId]): The new parent album ID,
            if present.
    """

    album_id: AlbumId
    new_name: Optional[str] = None
    new_parent_album_id: Optional[AlbumId] = None


class AlbumsRepository(ABC):
    """
    A class that represents a repository of albums.
    """

    @abstractmethod
    def get_album_by_id(self, id: AlbumId) -> Album:
        """
        Returns the album.

        Args:
            id (AlbumId): The album ID.

        Returns:
            Album: The album object.

        Raises:
            ValueError: If no album exists.
        """

    @abstractmethod
    def get_all_albums(self) -> list[Album]:
        '''
        Returns all of the albums in the system.

        Returns:
            list[Album]: A list of albums.
        '''

    @abstractmethod
    def create_album(
        self,
        album_name: str,
        parent_album_id: Optional[AlbumId],
    ) -> Album:
        '''
        Creates an album in a MongoDB client with the most amount of space remaining

        Args:
            album_name (str): The album name
            parent_album_id (Optional[AlbumId]): The parent album ID

        Returns:
            Album: An instance of the newly created album.
        '''

    @abstractmethod
    def delete_album(self, id: AlbumId):
        """
        Deletes a album.

        Args:
            client_id (str): The client ID.
            id (str): The album ID.

        Raises:
            ValueError: If no album exists.
        """

    @abstractmethod
    def delete_many_albums(self, ids: list[AlbumId]):
        """
        Deletes a list of albums from the database.

        Args:
            ids (list[AlbumId): The IDs of the albums to delete.

        Raises:
            ValueError: If a media item exists.
        """

    @abstractmethod
    def update_album(self, album_id: AlbumId, updated_album_fields: UpdatedAlbumFields):
        """
        Update an album with new fields.

        Args:
            album_id (AlbumId): The album ID.
            updated_album_fields (UpdatedAlbumFields): A set of updated album fields.
        """

    @abstractmethod
    def update_many_albums(self, requests: list[UpdateAlbumRequest]):
        '''
        Performs a bulk update on albums with new fields.

        Args:
            requests (list[UpdateAlbumRequest]): A list of album update requests.
        '''

    @abstractmethod
    def find_child_albums(self, album_id: AlbumId) -> list[Album]:
        '''
        Returns a list of child album IDs that are under an album.

        Args:
            album_id (AlbumId): The album ID
        '''

    @abstractmethod
    def count_child_albums(self, album_id: AlbumId) -> int:
        '''
        Returns the number of child albums in an album.

        Args:
            album_id (AlbumId): The album ID
        '''
