from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from bson.objectid import ObjectId
import concurrent

from ..shared.gphotos.clients_repository import GPhotosClientsRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
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
    '''
    Implementation of {@code GPhotosMediaItemUploader} that uploads media content to
    Google Photos in a single thread.
    '''

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


class GPhotosMediaItemParallelUploaderImpl:
    '''
    Implementation of {@code GPhotosMediaItemUploader} that uploads media content to
    Google Photos concurrently thread.
    '''

    def __init__(self, gphotos_client_repo: GPhotosClientsRepository):
        self.__gphotos_client_repo = gphotos_client_repo

    def upload_photos(self, upload_requests: list[UploadRequest]) -> list[str]:
        """
        Uploads a list of photos concurrently.

        Args:
            upload_requests (list[UploadRequest]): A list of upload requests

        Returns:
            list[str]: A list of Google Photo media item ids for each uploaded photo
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_request = {
                executor.submit(self.__upload_photo, request, index): request
                for index, request in enumerate(upload_requests)
            }

            media_item_ids = [''] * len(upload_requests)
            for future in concurrent.futures.as_completed(future_to_request):
                client_id, upload_token, index = future.result()
                client = self.__gphotos_client_repo.get_client_by_id(client_id)
                result = client.media_items().add_uploaded_photos_to_gphotos(
                    [upload_token]
                )
                media_item_ids[index] = result.newMediaItemResults[0].mediaItem.id

            return media_item_ids

    def __upload_photo(
        self, request: UploadRequest, index: int
    ) -> tuple[ObjectId, str, int]:
        client = self.__gphotos_client_repo.get_client_by_id(request.gphotos_client_id)
        upload_token = client.media_items().upload_photo_in_chunks(
            request.file_path, request.file_name
        )
        return (request.gphotos_client_id, upload_token, index)
