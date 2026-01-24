import unittest
from unittest.mock import MagicMock

from bson.objectid import ObjectId

from photos_drive.shared.core.media_items.media_item import MediaItem
from photos_drive.shared.core.media_items.media_item_id import MediaItemId
from photos_drive.shared.core.media_items.repository.base import (
    CreateMediaItemRequest,
    FindMediaItemRequest,
    MediaItemsRepository,
    UpdateMediaItemRequest,
)
from photos_drive.shared.core.media_items.repository.union import (
    UnionMediaItemsRepository,
)


class TestUnionMediaItemsRepository(unittest.TestCase):

    def setUp(self):
        self.client_id_1 = ObjectId()
        self.client_id_2 = ObjectId()

        self.mock_repo_1 = MagicMock(spec=MediaItemsRepository)
        self.mock_repo_1.get_client_id.return_value = self.client_id_1
        self.mock_repo_1.get_available_free_space.return_value = 1000

        self.mock_repo_2 = MagicMock(spec=MediaItemsRepository)
        self.mock_repo_2.get_client_id.return_value = self.client_id_2
        self.mock_repo_2.get_available_free_space.return_value = 2000

        self.repo = UnionMediaItemsRepository([self.mock_repo_1, self.mock_repo_2])

    def test_get_client_id_raises_error(self):
        with self.assertRaises(NotImplementedError):
            self.repo.get_client_id()

    def test_get_available_free_space_sums_results(self):
        self.assertEqual(self.repo.get_available_free_space(), 3000)

    def test_get_media_item_by_id_calls_correct_repo(self):
        media_item_id = MediaItemId(self.client_id_1, ObjectId())
        expected_item = MagicMock(spec=MediaItem)
        self.mock_repo_1.get_media_item_by_id.return_value = expected_item

        item = self.repo.get_media_item_by_id(media_item_id)

        self.assertEqual(item, expected_item)
        self.mock_repo_1.get_media_item_by_id.assert_called_once_with(media_item_id)
        self.mock_repo_2.get_media_item_by_id.assert_not_called()

    def test_get_media_item_by_id_unknown_client_raises_error(self):
        media_item_id = MediaItemId(ObjectId(), ObjectId())
        with self.assertRaisesRegex(ValueError, "No repository found for client"):
            self.repo.get_media_item_by_id(media_item_id)

    def test_get_all_media_items_aggregates_results(self):
        item_1 = MagicMock(spec=MediaItem)
        item_2 = MagicMock(spec=MediaItem)
        self.mock_repo_1.get_all_media_items.return_value = [item_1]
        self.mock_repo_2.get_all_media_items.return_value = [item_2]

        items = self.repo.get_all_media_items()

        self.assertCountEqual(items, [item_1, item_2])

    def test_find_media_items_aggregates_results(self):
        request = FindMediaItemRequest()
        item_1 = MagicMock(spec=MediaItem)
        item_2 = MagicMock(spec=MediaItem)
        self.mock_repo_1.find_media_items.return_value = [item_1]
        self.mock_repo_2.find_media_items.return_value = [item_2]

        items = self.repo.find_media_items(request)

        self.assertCountEqual(items, [item_1, item_2])
        self.mock_repo_1.find_media_items.assert_called_once_with(request)
        self.mock_repo_2.find_media_items.assert_called_once_with(request)

    def test_create_media_item_uses_repo_with_most_space(self):
        request = MagicMock(spec=CreateMediaItemRequest)
        expected_item = MagicMock(spec=MediaItem)
        self.mock_repo_2.create_media_item.return_value = expected_item

        item = self.repo.create_media_item(request)

        self.assertEqual(item, expected_item)
        self.mock_repo_2.create_media_item.assert_called_once_with(request)
        self.mock_repo_1.create_media_item.assert_not_called()

    def test_update_many_media_items_batches_by_client(self):
        id_1 = MediaItemId(self.client_id_1, ObjectId())
        id_2 = MediaItemId(self.client_id_2, ObjectId())
        req_1 = UpdateMediaItemRequest(media_item_id=id_1)
        req_2 = UpdateMediaItemRequest(media_item_id=id_2)

        self.repo.update_many_media_items([req_1, req_2])

        self.mock_repo_1.update_many_media_items.assert_called_once_with([req_1])
        self.mock_repo_2.update_many_media_items.assert_called_once_with([req_2])

    def test_delete_media_item_calls_correct_repo(self):
        media_item_id = MediaItemId(self.client_id_1, ObjectId())
        self.repo.delete_media_item(media_item_id)
        self.mock_repo_1.delete_media_item.assert_called_once_with(media_item_id)

    def test_delete_many_media_items_batches_by_client(self):
        id_1 = MediaItemId(self.client_id_1, ObjectId())
        id_2 = MediaItemId(self.client_id_2, ObjectId())
        self.repo.delete_many_media_items([id_1, id_2])

        self.mock_repo_1.delete_many_media_items.assert_called_once_with([id_1])
        self.mock_repo_2.delete_many_media_items.assert_called_once_with([id_2])
