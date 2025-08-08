from typing import Optional

from photos_drive.shared.blob_store.gphotos.albums import Album
from photos_drive.shared.blob_store.gphotos.albums_client import GPhotosAlbumsClient
from photos_drive.shared.blob_store.gphotos.testing.fake_items_repository import (
    FakeItemsRepository,
)


class FakeGPhotosAlbumsClient(GPhotosAlbumsClient):
    def __init__(self, id: str, repository: FakeItemsRepository):
        self.id = id
        self.repository = repository

    def list_albums(self) -> list[Album]:
        return self.repository.list_albums(self.id)

    def create_album(self, album_name: str) -> Album:
        return self.repository.create_album(self.id, album_name)

    def update_album(
        self,
        album_id: str,
        new_title: Optional[str] = None,
        new_cover_media_item_id: Optional[str] = None,
    ) -> Album:
        return self.repository.update_album(
            self.id, album_id, new_title, new_cover_media_item_id
        )

    def delete_album(self, album_id: str):
        return self.repository.delete_album(self.id, album_id)

    def add_photos_to_album(self, album_id: str, media_item_ids: list[str]):
        if len(media_item_ids) > 50:
            raise ValueError("Must have less than 50 media item ids")
        self.repository.add_photos_to_album(self.id, album_id, media_item_ids)

    def remove_photos_from_album(self, album_id: str, media_item_ids: list[str]):
        self.repository.remove_photos_from_album(self.id, album_id, media_item_ids)
