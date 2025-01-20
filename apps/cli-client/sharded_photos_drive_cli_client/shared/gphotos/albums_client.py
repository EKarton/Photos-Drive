import json
import logging
import backoff
from typing import Optional, Any
from requests.exceptions import RequestException

from dacite import from_dict
from google.auth.transport.requests import AuthorizedSession

from .albums import Album

logger = logging.getLogger(__name__)


class GPhotosAlbumsClient:
    def __init__(self, session: AuthorizedSession):
        self._session = session

    def list_albums(self, exclude_non_app_created_data: bool = False) -> list[Album]:
        """
        Returns a list of unshared albums.

        Args:
            exclude_non_app_created_data (bool): Whether to exclude albums not
                created by the app.

        Returns:
            list[Album]: A list of albums.
        """
        logger.debug("Listing albums")

        albums = []
        cur_page_token = None
        while True:
            res_json = self._list_albums_in_pages(
                cur_page_token, exclude_non_app_created_data
            )

            if "albums" not in res_json:
                break

            albums += res_json["albums"]

            if "nextPageToken" in res_json:
                cur_page_token = res_json["nextPageToken"]
            else:
                break

        return [from_dict(Album, a) for a in albums]

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def _list_albums_in_pages(
        self, page_token: str | None, exclude_non_app_created_data: bool
    ) -> Any:
        uri = "https://photoslibrary.googleapis.com/v1/albums"
        params = {
            "pageToken": page_token,
            "excludeNonAppCreatedData": exclude_non_app_created_data,
        }
        res = self._session.get(uri, params=params)
        res.raise_for_status()

        return res.json()

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def create_album(self, album_name: str) -> Album:
        """
        Creates an album with an album name.

        Args:
            album_name (str): The album name

        Returns:
            Album: The new album
        """
        logger.debug(f"Creating album {album_name}")

        request_body = json.dumps({"album": {"title": album_name}})
        uri = "https://photoslibrary.googleapis.com/v1/albums"
        res = self._session.post(uri, request_body)
        res.raise_for_status()

        return from_dict(Album, res.json())

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def update_album(
        self,
        album_id: str,
        new_title: Optional[str] = None,
        new_cover_media_item_id: Optional[str] = None,
    ) -> Album:
        """
        Updates an existing album with new properties.

        Args:
            album_id (str): The ID of the album to update.
            new_title (Optional[str]): The new title, if needed to change.
            new_cover_media_item_id (Optional[str]): The new cover of the album, if
                needed to change.

        Returns:
            Album: The new album object.
        """
        uri = f"https://photoslibrary.googleapis.com/v1/albums/{album_id}"

        if new_title is not None and new_cover_media_item_id is not None:
            uri += "?updateMask=title&updateMask=coverPhotoMediaItemId"
        elif new_title is not None:
            uri += "?updateMask=title"
        elif new_cover_media_item_id is not None:
            uri += "?updateMask=coverPhotoMediaItemId"

        request = {"title": new_title, "coverPhotoMediaItemId": new_cover_media_item_id}
        res = self._session.patch(uri, json.dumps(request))
        res.raise_for_status()

        return from_dict(Album, res.json())

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def add_photos_to_album(self, album_id: str, media_item_ids: list[str]):
        """
        Adds a list of media items from the album.

        Args:
            album_id (str): The album ID
            media_item_ids (list[str]): A list of media items to add, by their IDs
        """
        logger.debug(f"Add photos to album {album_id} {media_item_ids}")

        request_body = json.dumps({"mediaItemIds": media_item_ids})
        base_url = "https://photoslibrary.googleapis.com/v1/albums"
        uri = "{0}/{1}:batchAddMediaItems".format(base_url, album_id)
        res = self._session.post(uri, request_body)
        res.raise_for_status()

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def remove_photos_from_album(self, album_id: str, media_item_ids: list[str]):
        """
        Removes a list of media items from the album.

        Args:
            album_id (str): The album ID
            media_item_ids (list[str]): A list of media items to remove, by their IDs
        """
        logger.debug(f"Removing photos from album {album_id} {media_item_ids}")

        request_body = json.dumps({"mediaItemIds": media_item_ids})
        base_url = "https://photoslibrary.googleapis.com/v1/albums"
        uri = "{0}/{1}:batchRemoveMediaItems".format(base_url, album_id)
        res = self._session.post(uri, request_body)
        res.raise_for_status()
