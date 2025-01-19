from collections import defaultdict
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
                executor.submit(self.__upload_photo, request): request
                for request in upload_requests
            }

            upload_tokens_by_client = defaultdict(list)
            for future in concurrent.futures.as_completed(future_to_request):
                try:
                    client_id, upload_token = future.result()
                    upload_tokens_by_client[client_id].append(upload_token)
                except Exception as exc:
                    request = future_to_request[future]
                    logger.error(
                        f'Upload for {request.file_name} generated an exception: {exc}'
                    )
                    raise exc

        media_item_ids = []
        for client_id, tokens in upload_tokens_by_client.items():
            client = self.__gphotos_client_repo.get_client_by_id(client_id)
            for token in tokens:
                result = client.media_items().add_uploaded_photos_to_gphotos([token])
                media_item_ids.append(result.newMediaItemResults[0].mediaItem.id)

        return media_item_ids

    def __upload_photo(self, request: UploadRequest) -> tuple[ObjectId, str]:
        client = self.__gphotos_client_repo.get_client_by_id(request.gphotos_client_id)
        upload_token = client.media_items().upload_photo_in_chunks(
            request.file_path, request.file_name
        )
        return (request.gphotos_client_id, upload_token)
