from typing import Optional

from photos_drive.shared.blob_store.gphotos.media_items import (
    MediaItem,
    UploadedPhotosToGPhotosResult,
)
from photos_drive.shared.blob_store.gphotos.media_items_client import (
    GPhotosMediaItemsClient,
)
from photos_drive.shared.blob_store.gphotos.testing.fake_items_repository import (
    FakeItemsRepository,
)


class FakeGPhotosMediaItemsClient(GPhotosMediaItemsClient):
    def __init__(self, id: str, repository: FakeItemsRepository):
        self.id = id
        self.repository = repository

    def add_uploaded_photos_to_gphotos(
        self, upload_tokens: list[str], album_id: Optional[str] = None
    ) -> UploadedPhotosToGPhotosResult:
        if len(upload_tokens) >= 50:
            raise ValueError("Must have less than 50 upload tokens")

        return self.repository.add_uploaded_photos_to_gphotos(
            self.id, upload_tokens, album_id
        )

    def get_all_media_items(self) -> list[MediaItem]:
        return self.repository.get_all_media_items(self.id)

    def search_for_media_items(
        self,
        album_id: Optional[str] = None,
        filters: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> list[MediaItem]:
        return self.repository.search_for_media_items(
            self.id, album_id, filters, order_by
        )

    def get_media_item_by_id(self, media_item_id: str) -> MediaItem:
        return self.repository.get_media_item_by_id(self.id, media_item_id)

    def upload_photo(self, photo_file_path: str, file_name: str) -> str:
        return self.repository.upload_photo(self.id, photo_file_path, file_name)

    def upload_photo_in_chunks(self, photo_file_path: str, file_name: str) -> str:
        return self.repository.upload_photo(self.id, photo_file_path, file_name)
