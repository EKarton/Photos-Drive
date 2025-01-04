from typing import Optional
from ..albums_client import GPhotosAlbumsClient
from ..albums import Album
from .fake_items_repository import FakeItemsRepository


class FakeGPhotosAlbumsClient(GPhotosAlbumsClient):
    def __init__(self, id: str, repository: FakeItemsRepository):
        self.id = id
        self.repository = repository

    def list_albums(self, exclude_non_app_created_data: bool = False) -> list[Album]:
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

    def add_photos_to_album(self, album_id: str, media_item_ids: list[str]):
        if len(media_item_ids) > 50:
            raise Exception("Must have less than 50 media item ids")
        self.repository.add_photos_to_album(self.id, album_id, media_item_ids)

    def remove_photos_from_album(self, album_id: str, media_item_ids: list[str]):
        self.repository.remove_photos_from_album(self.id, album_id, media_item_ids)
