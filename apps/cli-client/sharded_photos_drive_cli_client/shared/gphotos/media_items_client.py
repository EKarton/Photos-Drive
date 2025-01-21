import json
import logging
import os
import backoff
import dacite
import magic
from typing import Optional
from requests import Response
from requests.exceptions import HTTPError, RequestException

from dacite import from_dict
from google.auth.transport.requests import AuthorizedSession
from google.auth.transport import DEFAULT_RETRYABLE_STATUS_CODES

from .media_items import UploadedPhotosToGPhotosResult, MediaItem, VideoProcessingStatus

logger = logging.getLogger(__name__)

DEFAULT_RETRYABLE_ERROR_CODES_FOR_UPLOADED_PHOTOS = set(
    [
        1,  # Cancelled
        2,  # Unknown
        4,  # DEADLINE_EXCEEDED,
        10,  # 409 Conflict
        12,  # 501 Not Implemented
        13,  # 500 Internal Server Error
        14,  # 503 Service Unavailable
        15,  # 500 Internal Server Error
    ]
)

ERROR_CODES_FOR_UPLOADED_PHOTOS_TO_MESSAGE = {
    1: "Cancelled",
    2: "UNKNOWN",
    3: "INVALID_ARGUMENT",
    4: "DEADLINE_EXCEEDED",
    5: "NOT_FOUND",
    7: "PERMISSION_DENIED",
    8: "RESOURCE_EXHAUSTED",
    9: "FAILED_PRECONDITION",
    10: "ABORTED",
    11: "OUT_OF_RANGE",
    12: "UNIMPLEMENTED",
    13: "INTERNAL",
    14: "UNAVAILABLE",
    15: "DATA_LOSS",
    16: "UNAUTHENTICATED",
}


class IllegalStateException(ValueError):
    """Exception raised when the state is invalid"""

    def __init__(self, message: str):
        super().__init__(message)


class GPhotosMediaItemsClient:
    def __init__(self, session: AuthorizedSession):
        self._session = session

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def add_uploaded_photos_to_gphotos(
        self, upload_tokens: list[str], album_id: Optional[str] = None
    ) -> UploadedPhotosToGPhotosResult:
        """
        Adds a list of uploaded photos to Google Photos.

        Args:
            upload_tokens (list[str]): A list of upload tokens for each uploaded photo.
            album_id (str): The album ID

        Returns:
            UploadedPhotosToGPhotosResult: The results from the operation.

        """
        logger.debug(f"Add uploaded photos {upload_tokens} to album {album_id}")

        create_body = json.dumps(
            {
                "albumId": album_id,
                "newMediaItems": [
                    {
                        "description": "",
                        "simpleMediaItem": {"uploadToken": upload_token},
                    }
                    for upload_token in upload_tokens
                ],
            },
            indent=4,
        )

        res = self._session.post(
            "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
            create_body,
        )
        res.raise_for_status()
        res_json = res.json()

        new_media_items = []
        for result in res_json["newMediaItemResults"]:
            if result["status"]["message"] == "Success":
                new_media_items.append(result)
            else:
                code = result["status"]["code"]
                message = result["status"]["message"]

                if code == 6:
                    continue
                elif code in DEFAULT_RETRYABLE_ERROR_CODES_FOR_UPLOADED_PHOTOS:
                    raise HTTPError(f"code: {code}, message: {message}")
                else:
                    raise ValueError(f"code: {code}, message: {message}")

        new_res = {"newMediaItemResults": new_media_items}
        return from_dict(
            UploadedPhotosToGPhotosResult,
            new_res,
            config=dacite.Config(cast=[VideoProcessingStatus]),
        )

    def search_for_media_items(
        self,
        album_id: Optional[str] = None,
        filters: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> list[MediaItem]:
        """
        Searches for media items.

        Args:
            album_id (Optional[str]): The album ID to search in, if present.
            filters (Optional[str]): A list of filters, if present.
            order_by (Optional[str]): The order to return the media items, if present.

        Returns:
            list[MediaItem]: A list of media items.
        """
        logger.debug(
            f"Listing media items with filter album_id={album_id} "
            + f"filters={filters} order_by={order_by}"
        )

        page_token = None
        media_items = []
        while True:
            res = self._search_media_items_in_pages(
                album_id, filters, order_by, page_token
            )
            res_body = res.json()

            if "mediaItems" not in res_body:
                break

            media_items += res_body["mediaItems"]

            if "nextPageToken" in res_body:
                page_token = res_body["nextPageToken"]
            else:
                break

        return [
            from_dict(MediaItem, m, config=dacite.Config(cast=[VideoProcessingStatus]))
            for m in media_items
        ]

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def _search_media_items_in_pages(
        self,
        album_id: Optional[str] | None,
        filters: Optional[object] | None,
        order_by: Optional[object] | None,
        page_token: Optional[str] | None,
    ) -> Response:
        res = self._session.post(
            "https://photoslibrary.googleapis.com/v1/mediaItems:search",
            json.dumps(
                {
                    "albumId": album_id,
                    "filters": filters,
                    "orderBy": order_by,
                    "pageToken": page_token,
                }
            ),
        )
        res.raise_for_status()
        return res

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def upload_photo(self, photo_file_path: str, file_name: str) -> str:
        """
        Uploads a photo not in chunks.

        Args:
            photo_file_path (str): The file path to the photo.
            file_name (str): The file name.

        Returns:
            str: The upload token.
        """
        logger.debug(f"Uploading photo {photo_file_path}")

        photo_file = open(photo_file_path, mode="rb")
        photo_bytes = photo_file.read()

        self._session.headers["Content-type"] = "application/octet-stream"
        self._session.headers["X-Goog-Upload-Protocol"] = "raw"
        self._session.headers["X-Goog-Upload-File-Name"] = file_name

        res = self._session.post(
            "https://photoslibrary.googleapis.com/v1/uploads", photo_bytes
        )
        res.raise_for_status()

        return res.content.decode()

    @backoff.on_exception(backoff.expo, (IllegalStateException), max_time=60)
    def upload_photo_in_chunks(
        self,
        photo_file_path: str,
        file_name: str,
    ) -> str:
        """
        Uploads a photo in chunks.

        Args:
            photo_file_path (str): The file path to the photo.
            file_name (str): The file name.

        Returns:
            str: The upload token.
        """
        upload_token = None
        mime_type = self._get_mime_type(photo_file_path)
        file_size_in_bytes = os.stat(photo_file_path).st_size

        logger.debug(
            f"Uploading {photo_file_path} in chunks "
            + f"({mime_type}, {file_size_in_bytes} bytes)"
        )

        res_1 = self._initialize_chunked_upload(
            mime_type, file_name, file_size_in_bytes
        )
        upload_url = res_1.headers["X-Goog-Upload-URL"]
        chunk_size = int(res_1.headers["X-Goog-Upload-Chunk-Granularity"])

        logger.debug(f"Obtained upload url and chunk size: {upload_url} {chunk_size}")

        num_bytes_uploaded = 0
        with open(photo_file_path, "rb") as file_obj:
            cur_offset = 0
            chunk = file_obj.read(chunk_size)
            while chunk:
                chunk_read = len(chunk)
                next_chunk = file_obj.read(chunk_size)

                # If there is no more chunks to read, then [chunk] is the last chunk
                is_last_chunk = not next_chunk

                logger.debug(
                    f"Uploading chunk: {cur_offset} {chunk_read} {is_last_chunk}"
                )

                res_2 = self._upload_photo_chunk(
                    upload_url, cur_offset, chunk, is_last_chunk
                )

                if res_2.status_code != 200:
                    logger.error(
                        f"Failed uploading chunk: {res_2.status_code} "
                        + f"{res_2.content.decode('utf-8', errors='replace')}"
                    )

                    req_3 = self._query_chunked_upload(upload_url)
                    logger.debug(f"Query chunked upload res: {req_3.headers}")
                    upload_status = req_3.headers["X-Goog-Upload-Status"]

                    if upload_status != "active":
                        raise IllegalStateException("Upload is no longer active")

                    size_received = 0
                    if "X-Goog-Upload-Size-Received" in req_3.headers:
                        size_received = int(
                            req_3.headers["X-Goog-Upload-Size-Received"]
                        )

                    logger.debug(f"Adjusted seek to {size_received}")
                    file_obj.seek(size_received, 0)
                    cur_offset = size_received
                    next_chunk = file_obj.read(chunk_size)
                else:
                    cur_offset += chunk_read
                    num_bytes_uploaded += chunk_read

                if is_last_chunk:
                    upload_token = res_2.content.decode()

                chunk = next_chunk

        logger.debug(f"Chunk uploading finished: {photo_file_path}")

        if not upload_token:
            raise ValueError("Failed to get upload token")

        return upload_token

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def _initialize_chunked_upload(
        self, mime_type: str, file_name: str, file_size_in_bytes: int
    ) -> Response:
        self._session.headers["Content-Length"] = "0"
        self._session.headers["X-Goog-Upload-Command"] = "start"
        self._session.headers["X-Goog-Upload-Content-Type"] = mime_type
        self._session.headers["X-Goog-Upload-Protocol"] = "resumable"
        self._session.headers["X-Goog-Upload-File-Name"] = file_name
        self._session.headers["X-Goog-Upload-Raw-Size"] = str(file_size_in_bytes)

        res = self._session.post("https://photoslibrary.googleapis.com/v1/uploads")
        res.raise_for_status()

        return res

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def _upload_photo_chunk(
        self, upload_url: str, cur_offset: int, chunk: bytes, is_last_chunk: bool
    ) -> Response:
        upload_cmd = "upload, finalize" if is_last_chunk else "upload"
        self._session.headers["X-Goog-Upload-Command"] = upload_cmd
        self._session.headers["X-Goog-Upload-Offset"] = str(cur_offset)

        res = self._session.post(upload_url, chunk)
        if res.status_code in DEFAULT_RETRYABLE_STATUS_CODES:
            res.raise_for_status()

        return res

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def _query_chunked_upload(self, upload_url) -> Response:
        self._session.headers["Content-Length"] = "0"
        self._session.headers["X-Goog-Upload-Command"] = "query"

        res = self._session.post(upload_url)
        res.raise_for_status()

        return res

    def _get_mime_type(self, file_path) -> str:
        return magic.from_file(file_path, mime=True)
