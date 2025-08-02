from abc import ABC, abstractmethod

from photos_drive.shared.metadata.media_item_id import MediaItemId
from photos_drive.shared.metadata.media_items import MediaItem


class MapCellsRepository(ABC):
    """
    A class that represents a repository of cells on a map.
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
