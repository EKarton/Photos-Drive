from datetime import datetime
import unittest
from unittest.mock import MagicMock

from bson import ObjectId

from photos_drive.shared.core.albums.album_id import AlbumId
from photos_drive.shared.core.media_items.gps_location import GpsLocation
from photos_drive.shared.core.media_items.media_item import MediaItem
from photos_drive.shared.core.media_items.media_item_id import MediaItemId
from photos_drive.shared.features.maps.repository.base import MapCellsRepository
from photos_drive.shared.features.maps.repository.union import UnionMapCellsRepository


class TestUnionMapCellsRepository(unittest.TestCase):

    def setUp(self):
        self.repo1 = MagicMock(spec=MapCellsRepository)
        self.repo1.get_client_id.return_value = ObjectId()
        self.repo1.get_available_free_space.return_value = 100

        self.repo2 = MagicMock(spec=MapCellsRepository)
        self.repo2.get_client_id.return_value = ObjectId()
        self.repo2.get_available_free_space.return_value = 500

        self.union_repo = UnionMapCellsRepository([self.repo1, self.repo2])

    def test_get_available_free_space(self):
        self.assertEqual(self.union_repo.get_available_free_space(), 600)

    def test_add_media_item__delegates_to_repo_with_most_space(self):
        media_item = MediaItem(
            id=MediaItemId(ObjectId(), ObjectId()),
            file_name="photo.jpg",
            location=GpsLocation(latitude=37.7749, longitude=-122.4194),
            file_hash=b"h1",
            gphotos_media_item_id="mid",
            gphotos_client_id=ObjectId(),
            album_id=AlbumId(ObjectId(), ObjectId()),
            width=100,
            height=100,
            date_taken=datetime.now(),
            embedding_id=None,
            mime_type="image/jpeg",
        )

        self.union_repo.add_media_item(media_item)

        self.repo2.add_media_item.assert_called_once_with(media_item)
        self.repo1.add_media_item.assert_not_called()

    def test_remove_media_item__delegates_to_all_repos(self):
        mid = MediaItemId(ObjectId(), ObjectId())
        self.union_repo.remove_media_item(mid)

        self.repo1.remove_media_item.assert_called_once_with(mid)
        self.repo2.remove_media_item.assert_called_once_with(mid)
