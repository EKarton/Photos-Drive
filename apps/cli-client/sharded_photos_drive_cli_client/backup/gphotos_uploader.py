from dataclasses import dataclass
from abc import ABC, abstractmethod
from bson.objectid import ObjectId

from ..shared.gphotos.clients_repository import GPhotosClientsRepository


@dataclass
class UploadRequest:
    file_path: str
    file_name: str
    gphotos_client_id: ObjectId


class GPhotosMediaItemUploader(ABC):
    '''A class responsible for uploading media content to Google Photos.'''

    @abstractmethod
    def upload_photos(self, upload_requests: list[UploadRequest]) -> list[str]:
        """
        Uploads a list of photos.

        Args:
            upload_requests (list[UploadRequest]): A list of upload requests

        Returns:
            list[str]: A list of Google Photo media item ids for each uploaded photo
        """


class GPhotosMediaItemUploaderImpl:
    '''Implementation of {@code GPhotosMediaItemUploader} that uploads media content to Google Photos in a single thread.'''

    def __init__(self, gphotos_client_repo: GPhotosClientsRepository):
        self.__gphotos_client_repo = gphotos_client_repo

    def upload_photos(self, upload_requests: list[UploadRequest]) -> list[str]:
        """
        Uploads a list of photos.

        Args:
            upload_requests (list[UploadRequest]): A list of upload requests

        Returns:
            list[str]: A list of Google Photo media item ids for each uploaded photo
        """
        media_item_ids = []

        for request in upload_requests:
            client = self.__gphotos_client_repo.get_client_by_id(
                request.gphotos_client_id
            )
            upload_token = client.media_items().upload_photo_in_chunks(
                request.file_path, request.file_name
            )
            upload_result = client.media_items().add_uploaded_photos_to_gphotos(
                [upload_token]
            )
            media_item_id = upload_result.newMediaItemResults[0].mediaItem.id
            media_item_ids.append(media_item_id)

        return media_item_ids
