from abc import ABC, abstractmethod

from bson.objectid import ObjectId

from photos_drive.shared.core.media_items.media_item import MediaItem
from photos_drive.shared.core.media_items.media_item_id import MediaItemId


class MapCellsRepository(ABC):
    """
    A class that represents a repository of cells on a map.
    """

    @abstractmethod
    def get_client_id(self) -> ObjectId:
        """
        Returns the client ID of the repository.

        Returns:
            ObjectId: the client ID of the repository.
        """

    @abstractmethod
    def get_available_free_space(self) -> int:
        """
        Returns the available free space in the repository.

        Returns:
            int: the available free space in the repository.
        """

    @abstractmethod
    def add_media_item(self, media_item: MediaItem):
        '''
        Adds a media item to the cells repository.
        '''

    @abstractmethod
    def remove_media_item(self, media_item_id: MediaItemId):
        '''
        Removes a media item from the cells repository.

        Args:
            media_item_id (MediaItemId): The ID of the media item to remove
        '''
