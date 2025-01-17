import unittest
from unittest.mock import Mock
from bson.objectid import ObjectId

from sharded_photos_drive_cli_client.shared.mongodb.media_items_repository import (
    MediaItemsRepositoryImpl,
    CreateMediaItemRequest,
    MongoDbClientsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.media_items import (
    MediaItemId,
    GpsLocation,
)
from sharded_photos_drive_cli_client.shared.mongodb.testing import (
    create_mock_mongo_client,
)


class TestMediaItemsRepositoryImpl(unittest.TestCase):

    def setUp(self):
        self.mock_clients_repo = Mock(spec=MongoDbClientsRepository)
        self.mock_client = create_mock_mongo_client()
        self.mock_clients_repo.get_client_by_id.return_value = self.mock_client
        self.mock_clients_repo.find_id_of_client_with_most_space.return_value = (
            ObjectId()
        )

        self.repo = MediaItemsRepositoryImpl(self.mock_clients_repo)

    def test_get_media_item_by_id(self):
        media_item_id = MediaItemId(ObjectId(), ObjectId())

        # Insert a mock media item into the mock database
        self.mock_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "_id": media_item_id.object_id,
                "file_name": "test_image.jpg",
                "hash_code": "abc123",
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": str(media_item_id.client_id),
                "gphotos_media_item_id": "gphotos_123",
            }
        )

        # Test retrieval
        media_item = self.repo.get_media_item_by_id(media_item_id)

        # Assert the retrieved media item matches the inserted data
        self.assertEqual(media_item.file_name, "test_image.jpg")
        self.assertEqual(media_item.hash_code, "abc123")
        self.assertIsNotNone(media_item.location)
        self.assertEqual(media_item.location, GpsLocation(56.78, 12.34))
        self.assertEqual(media_item.gphotos_client_id, media_item_id.client_id)
        self.assertEqual(media_item.gphotos_media_item_id, "gphotos_123")

    def test_get_media_item_by_id_not_found(self):
        media_item_id = MediaItemId(ObjectId(), ObjectId())

        with self.assertRaisesRegex(ValueError, "Media item .* does not exist!"):
            self.repo.get_media_item_by_id(media_item_id)

    def test_create_media_item(self):
        request = CreateMediaItemRequest(
            file_name="new_image.jpg",
            hash_code="hashcode123",
            location=GpsLocation(longitude=12.34, latitude=56.78),
            gphotos_client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
            gphotos_media_item_id="gphotos_456",
        )

        # Test creation of media item
        media_item = self.repo.create_media_item(request)

        # Assert that the media item was created correctly
        self.assertEqual(media_item.file_name, "new_image.jpg")
        self.assertEqual(media_item.hash_code, "hashcode123")
        self.assertIsNotNone(media_item.location)
        self.assertEqual(media_item.location, GpsLocation(56.78, 12.34))
        self.assertEqual(media_item.gphotos_client_id, request.gphotos_client_id)
        self.assertEqual(
            media_item.gphotos_media_item_id, request.gphotos_media_item_id
        )

    def test_delete_media_item(self):
        # Insert a mock media item into the mock database
        media_item_id = MediaItemId(ObjectId(), ObjectId())
        self.mock_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "_id": media_item_id.object_id,
                "file_name": "to_delete.jpg",
                "hash_code": "hashcode456",
                "gphotos_client_id": str(media_item_id.client_id),
                "gphotos_media_item_id": "gphotos_789",
            }
        )

        # Test deletion
        self.repo.delete_media_item(media_item_id)

        # Assert that the media item has been deleted
        deleted_media = self.mock_client["sharded_google_photos"][
            "media_items"
        ].find_one({"_id": media_item_id.object_id})
        self.assertIsNone(deleted_media)

    def test_delete_media_item_not_found(self):
        media_item_id = MediaItemId(ObjectId(), ObjectId())

        with self.assertRaisesRegex(
            ValueError, "Unable to delete media item: .* not found"
        ):
            self.repo.delete_media_item(media_item_id)

    def test_delete_many_media_items(self):
        ids_to_delete = [
            MediaItemId(ObjectId(), ObjectId()),
            MediaItemId(ObjectId(), ObjectId()),
        ]

        # Insert mock media items into the mock database
        for mid in ids_to_delete:
            self.mock_client["sharded_google_photos"]["media_items"].insert_one(
                {
                    "_id": mid.object_id,
                    "file_name": f"delete_me_{mid.object_id}.jpg",
                    "hash_code": f"hashcode_{mid.object_id}",
                    "gphotos_client_id": str(mid.client_id),
                    "gphotos_media_item_id": f"gphotos_{mid.object_id}",
                }
            )

        # Test deletion of multiple items
        self.repo.delete_many_media_items(ids_to_delete)

        # Assert that all items have been deleted
        for mid in ids_to_delete:
            deleted_media = self.mock_client["sharded_google_photos"][
                "media_items"
            ].find_one({"_id": mid.object_id})
            self.assertIsNone(deleted_media)

    def test_delete_many_media_items_partial_failure(self):
        ids_to_delete = [
            MediaItemId(ObjectId(), ObjectId()),
            MediaItemId(ObjectId(), ObjectId()),
        ]

        # Insert one mock item into the database but not the other
        existing_mid = ids_to_delete[0]

        self.mock_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "_id": existing_mid.object_id,
                "file_name": f"existing_{existing_mid.object_id}.jpg",
                "hash_code": f"hashcode_{existing_mid.object_id}",
                "gphotos_client_id": str(existing_mid.client_id),
                "gphotos_media_item_id": f"gphotos_{existing_mid.object_id}",
            }
        )

        with self.assertRaisesRegex(
            ValueError, "Unable to delete all media items in .*"
        ):
            self.repo.delete_many_media_items(ids_to_delete)
