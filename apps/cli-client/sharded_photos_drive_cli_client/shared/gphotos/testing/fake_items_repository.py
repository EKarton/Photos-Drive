import threading
import uuid
from dacite import from_dict
from typing import Optional

from sharded_photos_drive_cli_client.shared.utils.synchronized import synchronized

from ..albums import Album
from ..media_items import UploadedPhotosToGPhotosResult, MediaItem


class FakeItemsRepository:
    _lock = threading.RLock()

    def __init__(self):
        self.__album_id_to_album = {}
        self.__album_id_to_media_item_ids = {}
        self.__album_id_to_accessible_client_ids = {}
        self.__album_id_to_owned_client_id = {}

        self.__media_item_id_to_media_item = {}
        self.__media_item_ids_to_owned_client_id = {}
        self.__upload_tokens_to_file_name = {}
        self.__media_item_ids_to_accessible_client_ids = {}

    def list_albums(self, client_id: str) -> list[Album]:
        def is_allowed(album):
            is_shared = album["shareInfo"] is None
            is_accessible = (
                client_id in self.__album_id_to_accessible_client_ids[album["id"]]
            )
            return is_shared and is_accessible

        return [
            from_dict(Album, a)
            for a in filter(is_allowed, self.__album_id_to_album.values())
        ]

    @synchronized(_lock)
    def create_album(self, client_id: str, album_name: str) -> Album:
        new_album_id = self.__get_unique_album_id()
        new_album = {
            "id": new_album_id,
            "title": album_name,
            "productUrl": f"http://google.com/albums/{new_album_id}",
            "isWriteable": True,
            "shareInfo": None,
            "mediaItemsCount": "0",
            "coverPhotoBaseUrl": None,
            "coverPhotoMediaItemId": None,
        }
        self.__album_id_to_album[new_album_id] = new_album
        self.__album_id_to_media_item_ids[new_album_id] = set()
        self.__album_id_to_accessible_client_ids[new_album_id] = set([client_id])
        self.__album_id_to_owned_client_id[new_album_id] = client_id

        return from_dict(
            Album,
            {
                "id": new_album["id"],
                "title": new_album["title"],
                "productUrl": new_album["productUrl"],
                "isWriteable": new_album["isWriteable"],
            },
        )

    @synchronized(_lock)
    def add_photos_to_album(
        self, client_id: str, album_id: str, media_item_ids: list[str]
    ):
        if client_id not in self.__album_id_to_accessible_client_ids[album_id]:
            raise Exception("Cannot add photos to album it did not join")

        for media_id in media_item_ids:
            if (
                client_id
                not in self.__media_item_ids_to_accessible_client_ids[media_id]
            ):
                raise Exception("Cannot put someone's media item into album")

            self.__album_id_to_media_item_ids[album_id].add(media_id)

    @synchronized(_lock)
    def remove_photos_from_album(
        self, client_id: str, album_id: str, media_item_ids: list[str]
    ):
        if client_id not in self.__album_id_to_accessible_client_ids[album_id]:
            raise Exception("Cannot remove photos from album it did not join")

        for media_id in media_item_ids:
            is_accessible = (
                client_id in self.__media_item_ids_to_accessible_client_ids[media_id]
            )
            if not is_accessible:
                raise Exception("Cannot remove someone else's photos from album")

            self.__album_id_to_media_item_ids[album_id].remove(media_id)

    @synchronized(_lock)
    def add_uploaded_photos_to_gphotos(
        self, client_id: str, upload_tokens: list[str], album_id: Optional[str] = None
    ) -> UploadedPhotosToGPhotosResult:
        new_media_items_results = []
        for upload_token in upload_tokens:
            new_media_item_id = self.__get_unique_media_item_id()

            if album_id is not None:
                if client_id not in self.__album_id_to_accessible_client_ids[album_id]:
                    raise Exception("Cannot add uploaded photos to inaccessible album")
                self.__album_id_to_media_item_ids[album_id].add(new_media_item_id)

            new_media_item = {
                "id": new_media_item_id,
                "description": "New photo",
                "productUrl": f"http://google.com/photos/{new_media_item_id}",
                "baseUrl": f"http://google.com/photos/{new_media_item_id}",
                "mimeType": "jpeg",
                "mediaMetadata": {
                    "creationTime": "2014-10-02T15:01:23Z",
                    "width": "200px",
                    "height": "300px",
                    "photo": {
                        "cameraMake": "IPhone",
                        "cameraModel": "14 Pro",
                        "focalLength": 50,
                        "apertureFNumber": 1.4,
                        "isoEquivalent": 400,
                        "exposureTime": "0.005s",
                    },
                },
                "contributorInfo": {
                    "profilePictureBaseUrl": "http://google.com/profile/1",
                    "displayName": "Bob Smith",
                },
                "filename": self.__upload_tokens_to_file_name[upload_token],
            }

            self.__media_item_id_to_media_item[new_media_item_id] = new_media_item
            self.__media_item_ids_to_accessible_client_ids[new_media_item_id] = set(
                [client_id]
            )
            self.__media_item_ids_to_owned_client_id[new_media_item_id] = client_id

            new_media_items_results.append(
                {
                    "uploadToken": upload_token,
                    "status": {"code": 200, "message": "Success", "details": []},
                    "mediaItem": new_media_item,
                }
            )

        return from_dict(
            UploadedPhotosToGPhotosResult,
            {"newMediaItemResults": new_media_items_results},
        )

    @synchronized(_lock)
    def upload_photo(self, client_id: str, photo_file_path: str, file_name: str) -> str:
        upload_token = self.__get_unique_token()
        self.__upload_tokens_to_file_name[upload_token] = file_name
        return upload_token

    def search_for_media_items(
        self,
        client_id: str,
        album_id: Optional[str] = None,
        filters: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> list[MediaItem]:
        if album_id is not None:
            if client_id not in self.__album_id_to_accessible_client_ids[album_id]:
                raise Exception("Cannot search in inaccessible album")

            return [
                from_dict(MediaItem, self.__media_item_id_to_media_item[media_item_id])
                for media_item_id in self.__album_id_to_media_item_ids[album_id]
            ]
        else:

            def is_valid(media_item):
                is_owned = (
                    client_id
                    == self.__media_item_ids_to_owned_client_id[media_item["id"]]
                )
                return is_owned

            all_media_items = list(self.__media_item_id_to_media_item.values())
            return [from_dict(MediaItem, a) for a in filter(is_valid, all_media_items)]

    @synchronized(_lock)
    def update_album(
        self,
        client_id: str,
        album_id: str,
        new_title: Optional[str] = None,
        new_cover_media_item_id: Optional[str] = None,
    ) -> Album:
        if client_id != self.__album_id_to_owned_client_id[album_id]:
            raise Exception("Cannot update album it does not own")

        album_info = self.__album_id_to_album[album_id]
        if new_title is not None:
            album_info["title"] = new_title
        if new_cover_media_item_id is not None:
            album_info["coverPhotoMediaItemId"] = new_cover_media_item_id
            album_info["coverPhotoBaseUrl"] = (
                f"http://google.com/photos/{new_cover_media_item_id}"
            )

        return from_dict(
            Album,
            {
                "id": album_info["id"],
                "title": album_info["title"],
                "productUrl": album_info["productUrl"],
                "isWriteable": album_info["isWriteable"],
                "mediaItemsCount": album_info["mediaItemsCount"],
                "coverPhotoBaseUrl": album_info["coverPhotoBaseUrl"],
                "coverPhotoMediaItemId": album_info["coverPhotoMediaItemId"],
            },
        )

    def __get_unique_media_item_id(self):
        media_item_id = str(uuid.uuid4())
        while media_item_id in self.__media_item_id_to_media_item:
            media_item_id = str(uuid.uuid4())

        return media_item_id

    def __get_unique_token(self):
        token = str(uuid.uuid4())
        while token in self.__upload_tokens_to_file_name:
            token = str(uuid.uuid4())

        return token

    def __get_unique_album_id(self):
        album_id = str(uuid.uuid4())
        while album_id in self.__album_id_to_album:
            album_id = str(uuid.uuid4())

        return album_id
