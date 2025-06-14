from datetime import datetime
import os
from bson import Binary
import unittest
from bson.objectid import ObjectId

from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.mongodb.media_items_repository_impl import (
    MediaItemsRepositoryImpl,
)
from photos_drive.shared.metadata.album_id import (
    AlbumId,
    album_id_to_string,
)
from photos_drive.shared.metadata.media_item_id import MediaItemId
from photos_drive.shared.metadata.media_items_repository import (
    FindMediaItemRequest,
    CreateMediaItemRequest,
    UpdateMediaItemRequest,
)
from photos_drive.shared.metadata.media_items import (
    GpsLocation,
)
from photos_drive.shared.metadata.mongodb.testing import (
    create_mock_mongo_client,
)

MOCK_FILE_HASH = b'\x8a\x19\xdd\xdeg\xdd\x96\xf2'

MOCK_ALBUM_ID = AlbumId(
    ObjectId("5f50c31e8a7d4b1c9c9b0b22"),
    ObjectId("5f50c31e8a7d4b1c9c9b0b23"),
)

MOCK_ALBUM_ID_2 = AlbumId(
    ObjectId("5f50c31e8a7d4b1c9c9b0c12"),
    ObjectId("5f50c31e8a7d4b1c9c9b0c13"),
)

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0)

MOCK_DATE_TAKEN_2 = datetime(2026, 1, 1, 14, 30, 0)


class TestMediaItemsRepositoryImpl(unittest.TestCase):

    def setUp(self):
        self.mongodb_client_id = ObjectId()
        self.mongodb_client = create_mock_mongo_client()
        self.mongodb_clients_repo = MongoDbClientsRepository()
        self.mongodb_clients_repo.add_mongodb_client(
            self.mongodb_client_id, self.mongodb_client
        )
        self.repo = MediaItemsRepositoryImpl(self.mongodb_clients_repo)

    def test_get_media_item_by_id(self):
        fake_file_hash = os.urandom(16)
        media_item_id = MediaItemId(self.mongodb_client_id, ObjectId())

        # Insert a mock media item into the mock database
        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "_id": media_item_id.object_id,
                "file_name": "test_image.jpg",
                "file_hash": Binary(fake_file_hash),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": str(media_item_id.client_id),
                "gphotos_media_item_id": "gphotos_123",
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )

        # Test retrieval
        media_item = self.repo.get_media_item_by_id(media_item_id)

        # Assert the retrieved media item matches the inserted data
        self.assertEqual(media_item.file_name, "test_image.jpg")
        self.assertEqual(media_item.file_hash, fake_file_hash)
        self.assertIsNotNone(media_item.location)
        self.assertEqual(media_item.location, GpsLocation(56.78, 12.34))
        self.assertEqual(media_item.gphotos_client_id, media_item_id.client_id)
        self.assertEqual(media_item.gphotos_media_item_id, "gphotos_123")
        self.assertEqual(media_item.width, 100)
        self.assertEqual(media_item.height, 200)
        self.assertEqual(media_item.date_taken, MOCK_DATE_TAKEN)

    def test_get_media_item_by_id_not_found(self):
        media_item_id = MediaItemId(self.mongodb_client_id, ObjectId())

        with self.assertRaisesRegex(ValueError, "Media item .* does not exist!"):
            self.repo.get_media_item_by_id(media_item_id)

    def test_get_all_media_items(self):
        fake_file_hash = os.urandom(16)

        # Insert a mock media item into the mock database
        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image.jpg",
                "file_hash": Binary(fake_file_hash),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": str(self.mongodb_client_id),
                "gphotos_media_item_id": "gphotos_123",
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )

        # Test retrieval
        media_items = self.repo.get_all_media_items()

        # Assert the retrieved media item matches the inserted data
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].file_name, "test_image.jpg")
        self.assertEqual(media_items[0].file_hash, fake_file_hash)
        self.assertIsNotNone(media_items[0].location)
        self.assertEqual(media_items[0].location, GpsLocation(56.78, 12.34))
        self.assertEqual(media_items[0].gphotos_client_id, self.mongodb_client_id)
        self.assertEqual(media_items[0].gphotos_media_item_id, "gphotos_123")
        self.assertEqual(media_items[0].width, 100)
        self.assertEqual(media_items[0].height, 200)
        self.assertEqual(media_items[0].date_taken, MOCK_DATE_TAKEN)

    def test_find_media_items(self):
        # Insert mock media items from different albums into the mock database
        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image.jpg",
                "file_hash": Binary(os.urandom(16)),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": str(self.mongodb_client_id),
                "gphotos_media_item_id": "gphotos_1234",
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )
        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image_1.jpg",
                "file_hash": Binary(os.urandom(16)),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": str(self.mongodb_client_id),
                "gphotos_media_item_id": "gphotos_123",
                "album_id": album_id_to_string(MOCK_ALBUM_ID_2),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )
        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image_2.jpg",
                "file_hash": Binary(os.urandom(16)),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": str(self.mongodb_client_id),
                "gphotos_media_item_id": "gphotos_12345",
                "album_id": album_id_to_string(MOCK_ALBUM_ID_2),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )

        media_items = self.repo.find_media_items(
            FindMediaItemRequest(album_id=MOCK_ALBUM_ID_2, file_name='test_image_2.jpg')
        )

        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].album_id, MOCK_ALBUM_ID_2)
        self.assertEqual(media_items[0].file_name, 'test_image_2.jpg')
        self.assertEqual(media_items[0].gphotos_media_item_id, 'gphotos_12345')
        self.assertEqual(media_items[0].width, 100)
        self.assertEqual(media_items[0].height, 200)
        self.assertEqual(media_items[0].date_taken, MOCK_DATE_TAKEN)

    def test_find_media_items_in_different_databases(self):
        mongodb_client_id_1 = ObjectId()
        mongodb_client_1 = create_mock_mongo_client()
        mongodb_client_id_2 = ObjectId()
        mongodb_client_2 = create_mock_mongo_client()
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(mongodb_client_id_1, mongodb_client_1)
        mongodb_clients_repo.add_mongodb_client(mongodb_client_id_2, mongodb_client_2)
        repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        mongodb_client_1["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image.jpg",
                "file_hash": Binary(os.urandom(16)),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": ObjectId(),
                "gphotos_media_item_id": "gphotos_1234",
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )
        mongodb_client_2["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image_1.jpg",
                "file_hash": Binary(os.urandom(16)),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": ObjectId(),
                "gphotos_media_item_id": "gphotos_123",
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )
        mongodb_client_2["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image_2.jpg",
                "file_hash": Binary(os.urandom(16)),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": ObjectId(),
                "gphotos_media_item_id": "gphotos_12345",
                "album_id": album_id_to_string(MOCK_ALBUM_ID_2),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )

        media_items = repo.find_media_items(
            FindMediaItemRequest(mongodb_client_ids=[mongodb_client_id_2])
        )

        self.assertEqual(len(media_items), 2)
        self.assertEqual(media_items[0].album_id, MOCK_ALBUM_ID)
        self.assertEqual(media_items[0].file_name, 'test_image_1.jpg')
        self.assertEqual(media_items[1].album_id, MOCK_ALBUM_ID_2)
        self.assertEqual(media_items[1].file_name, 'test_image_2.jpg')
        self.assertEqual(media_items[1].width, 100)
        self.assertEqual(media_items[1].height, 200)
        self.assertEqual(media_items[1].date_taken, MOCK_DATE_TAKEN)

    def test_get_num_media_items_in_album(self):
        # Insert mock media items from different albums into the mock database
        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image.jpg",
                "file_hash": Binary(os.urandom(16)),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": ObjectId(),
                "gphotos_media_item_id": "gphotos_1234",
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )
        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image_1.jpg",
                "file_hash": Binary(os.urandom(16)),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": ObjectId(),
                "gphotos_media_item_id": "gphotos_123",
                "album_id": album_id_to_string(MOCK_ALBUM_ID_2),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )
        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "file_name": "test_image_2.jpg",
                "file_hash": Binary(os.urandom(16)),
                "location": {"type": "Point", "coordinates": [12.34, 56.78]},
                "gphotos_client_id": ObjectId(),
                "gphotos_media_item_id": "gphotos_12345",
                "album_id": album_id_to_string(MOCK_ALBUM_ID_2),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )

        self.assertEqual(self.repo.get_num_media_items_in_album(MOCK_ALBUM_ID), 1)
        self.assertEqual(self.repo.get_num_media_items_in_album(MOCK_ALBUM_ID_2), 2)

    def test_create_media_item(self):
        fake_file_hash = os.urandom(16)
        request = CreateMediaItemRequest(
            file_name="new_image.jpg",
            file_hash=fake_file_hash,
            location=GpsLocation(longitude=12.34, latitude=56.78),
            gphotos_client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
            gphotos_media_item_id="gphotos_456",
            album_id=MOCK_ALBUM_ID,
            width=100,
            height=200,
            date_taken=MOCK_DATE_TAKEN,
        )

        # Test creation of media item
        media_item = self.repo.create_media_item(request)

        # Assert that the media item was created correctly
        self.assertEqual(media_item.id.client_id, self.mongodb_client_id)
        self.assertEqual(media_item.file_name, "new_image.jpg")
        self.assertEqual(media_item.file_hash, fake_file_hash)
        self.assertIsNotNone(media_item.location)
        self.assertEqual(media_item.location, GpsLocation(56.78, 12.34))
        self.assertEqual(media_item.gphotos_client_id, request.gphotos_client_id)
        self.assertEqual(
            media_item.gphotos_media_item_id, request.gphotos_media_item_id
        )
        self.assertEqual(media_item.width, 100)
        self.assertEqual(media_item.height, 200)
        self.assertEqual(media_item.date_taken, MOCK_DATE_TAKEN)

    def test_update_media_item(self):
        media_item_1 = self.repo.create_media_item(
            CreateMediaItemRequest(
                'dog.jpg',
                MOCK_FILE_HASH,
                GpsLocation(longitude=12.34, latitude=56.78),
                gphotos_client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
                gphotos_media_item_id="gphotos_456",
                album_id=MOCK_ALBUM_ID,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
            )
        )

        new_file_hash = b'\x8b\x19\xdd\xdeg\xdd\x96\xf0'
        new_gphotos_client_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1c")
        self.repo.update_media_item(
            UpdateMediaItemRequest(
                media_item_id=media_item_1.id,
                new_file_name="dog1.jpg",
                new_file_hash=new_file_hash,
                clear_location=False,
                new_location=GpsLocation(latitude=10, longitude=20),
                new_gphotos_client_id=new_gphotos_client_id,
                new_gphotos_media_item_id="gphotos_1",
                new_width=300,
                new_height=400,
                new_date_taken=MOCK_DATE_TAKEN_2,
            ),
        )

        new_media_item_1 = self.repo.get_media_item_by_id(media_item_1.id)
        self.assertEqual(new_media_item_1.id, media_item_1.id)
        self.assertEqual(new_media_item_1.file_name, 'dog1.jpg')
        self.assertEqual(new_media_item_1.file_hash, new_file_hash)
        self.assertEqual(
            new_media_item_1.location, GpsLocation(latitude=10, longitude=20)
        )
        self.assertEqual(new_media_item_1.gphotos_client_id, new_gphotos_client_id)
        self.assertEqual(new_media_item_1.gphotos_media_item_id, 'gphotos_1')
        self.assertEqual(new_media_item_1.width, 300)
        self.assertEqual(new_media_item_1.height, 400)
        self.assertEqual(new_media_item_1.date_taken, MOCK_DATE_TAKEN_2)

    def test_update_many_media_items(self):
        media_item_1 = self.repo.create_media_item(
            CreateMediaItemRequest(
                'dog.jpg',
                MOCK_FILE_HASH,
                GpsLocation(longitude=12.34, latitude=56.78),
                gphotos_client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
                gphotos_media_item_id="gphotos_456",
                album_id=MOCK_ALBUM_ID,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
            )
        )
        media_item_2 = self.repo.create_media_item(
            CreateMediaItemRequest(
                'cat.jpg',
                MOCK_FILE_HASH,
                GpsLocation(longitude=2, latitude=3),
                gphotos_client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
                gphotos_media_item_id="gphotos_456",
                album_id=MOCK_ALBUM_ID,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
            )
        )

        new_file_hash = b'\x8b\x19\xdd\xdeg\xdd\x96\xf0'
        new_gphotos_client_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1c")
        self.repo.update_many_media_items(
            [
                UpdateMediaItemRequest(
                    media_item_id=media_item_1.id,
                    new_file_name="dog1.jpg",
                    new_file_hash=new_file_hash,
                    clear_location=False,
                    new_location=GpsLocation(latitude=10, longitude=20),
                    new_gphotos_client_id=new_gphotos_client_id,
                    new_gphotos_media_item_id="gphotos_1",
                    new_album_id=MOCK_ALBUM_ID_2,
                    new_width=300,
                    new_height=400,
                    new_date_taken=MOCK_DATE_TAKEN_2,
                ),
                UpdateMediaItemRequest(
                    media_item_id=media_item_2.id,
                    new_file_name="cat1.jpg",
                    new_file_hash=new_file_hash,
                    clear_location=False,
                    new_location=GpsLocation(latitude=20, longitude=30),
                    new_gphotos_client_id=new_gphotos_client_id,
                    new_gphotos_media_item_id="gphotos_1",
                    new_album_id=MOCK_ALBUM_ID_2,
                    new_width=300,
                    new_height=400,
                    new_date_taken=MOCK_DATE_TAKEN_2,
                ),
            ]
        )

        new_media_item_1 = self.repo.get_media_item_by_id(media_item_1.id)
        self.assertEqual(new_media_item_1.id, media_item_1.id)
        self.assertEqual(new_media_item_1.file_name, 'dog1.jpg')
        self.assertEqual(new_media_item_1.file_hash, new_file_hash)
        self.assertEqual(
            new_media_item_1.location, GpsLocation(latitude=10, longitude=20)
        )
        self.assertEqual(new_media_item_1.gphotos_client_id, new_gphotos_client_id)
        self.assertEqual(new_media_item_1.gphotos_media_item_id, 'gphotos_1')
        self.assertEqual(new_media_item_1.album_id, MOCK_ALBUM_ID_2)
        self.assertEqual(new_media_item_1.width, 300)
        self.assertEqual(new_media_item_1.height, 400)
        self.assertEqual(new_media_item_1.date_taken, MOCK_DATE_TAKEN_2)

        new_media_item_2 = self.repo.get_media_item_by_id(media_item_2.id)
        self.assertEqual(new_media_item_2.id, media_item_2.id)
        self.assertEqual(new_media_item_2.file_name, 'cat1.jpg')
        self.assertEqual(new_media_item_2.file_hash, new_file_hash)
        self.assertEqual(
            new_media_item_2.location, GpsLocation(latitude=20, longitude=30)
        )
        self.assertEqual(new_media_item_2.gphotos_client_id, new_gphotos_client_id)
        self.assertEqual(new_media_item_2.gphotos_media_item_id, 'gphotos_1')
        self.assertEqual(new_media_item_2.album_id, MOCK_ALBUM_ID_2)
        self.assertEqual(new_media_item_2.width, 300)
        self.assertEqual(new_media_item_2.height, 400)
        self.assertEqual(new_media_item_2.date_taken, MOCK_DATE_TAKEN_2)

    def test_update_many_media_items_update_file_name(self):
        media_item_1 = self.repo.create_media_item(
            CreateMediaItemRequest(
                'dog.jpg',
                MOCK_FILE_HASH,
                GpsLocation(longitude=12.34, latitude=56.78),
                gphotos_client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
                gphotos_media_item_id="gphotos_456",
                album_id=MOCK_ALBUM_ID,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
            )
        )

        self.repo.update_many_media_items(
            [
                UpdateMediaItemRequest(
                    media_item_id=media_item_1.id, new_file_name="cat.jpg"
                )
            ]
        )

        new_media_item_1 = self.repo.get_media_item_by_id(media_item_1.id)
        self.assertEqual(new_media_item_1.id, media_item_1.id)
        self.assertEqual(new_media_item_1.file_name, "cat.jpg")
        self.assertEqual(new_media_item_1.file_hash, media_item_1.file_hash)
        self.assertEqual(new_media_item_1.location, media_item_1.location)
        self.assertEqual(
            new_media_item_1.gphotos_client_id, media_item_1.gphotos_client_id
        )
        self.assertEqual(
            new_media_item_1.gphotos_media_item_id, media_item_1.gphotos_media_item_id
        )
        self.assertEqual(new_media_item_1.width, 100)
        self.assertEqual(new_media_item_1.height, 200)
        self.assertEqual(new_media_item_1.date_taken, MOCK_DATE_TAKEN)

    def test_update_many_media_items_clear_location(self):
        media_item_1 = self.repo.create_media_item(
            CreateMediaItemRequest(
                'dog.jpg',
                MOCK_FILE_HASH,
                GpsLocation(longitude=12.34, latitude=56.78),
                gphotos_client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
                gphotos_media_item_id="gphotos_456",
                album_id=MOCK_ALBUM_ID,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
            )
        )

        self.repo.update_many_media_items(
            [UpdateMediaItemRequest(media_item_id=media_item_1.id, clear_location=True)]
        )

        new_media_item_1 = self.repo.get_media_item_by_id(media_item_1.id)
        self.assertIsNone(new_media_item_1.location)

    def test_delete_media_item(self):
        # Insert a mock media item into the mock database
        media_item_id = MediaItemId(self.mongodb_client_id, ObjectId())
        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "_id": media_item_id.object_id,
                "file_name": "to_delete.jpg",
                "file_hash": Binary(os.urandom(16)),
                "gphotos_client_id": str(media_item_id.client_id),
                "gphotos_media_item_id": "gphotos_789",
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )

        # Test deletion
        self.repo.delete_media_item(media_item_id)

        # Assert that the media item has been deleted
        deleted_media = self.mongodb_client["sharded_google_photos"][
            "media_items"
        ].find_one({"_id": media_item_id.object_id})
        self.assertIsNone(deleted_media)

    def test_delete_media_item_not_found(self):
        media_item_id = MediaItemId(self.mongodb_client_id, ObjectId())

        with self.assertRaisesRegex(
            ValueError, "Unable to delete media item: .* not found"
        ):
            self.repo.delete_media_item(media_item_id)

    def test_delete_many_media_items(self):
        ids_to_delete = [
            MediaItemId(self.mongodb_client_id, ObjectId()),
            MediaItemId(self.mongodb_client_id, ObjectId()),
        ]

        # Insert mock media items into the mock database
        for mid in ids_to_delete:
            self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
                {
                    "_id": mid.object_id,
                    "file_name": f"delete_me_{mid.object_id}.jpg",
                    "file_hash": f"hashcode_{mid.object_id}",
                    "gphotos_client_id": str(mid.client_id),
                    "gphotos_media_item_id": f"gphotos_{mid.object_id}",
                    "album_id": album_id_to_string(MOCK_ALBUM_ID),
                    "width": 100,
                    "height": 200,
                    "date_taken": MOCK_DATE_TAKEN,
                }
            )

        # Test deletion of multiple items
        self.repo.delete_many_media_items(ids_to_delete)

        # Assert that all items have been deleted
        for mid in ids_to_delete:
            deleted_media = self.mongodb_client["sharded_google_photos"][
                "media_items"
            ].find_one({"_id": mid.object_id})
            self.assertIsNone(deleted_media)

    def test_delete_many_media_items_partial_failure(self):
        ids_to_delete = [
            MediaItemId(self.mongodb_client_id, ObjectId()),
            MediaItemId(self.mongodb_client_id, ObjectId()),
        ]

        # Insert one mock item into the database but not the other
        existing_mid = ids_to_delete[0]

        self.mongodb_client["sharded_google_photos"]["media_items"].insert_one(
            {
                "_id": existing_mid.object_id,
                "file_name": f"existing_{existing_mid.object_id}.jpg",
                "file_hash": Binary(os.urandom(16)),
                "gphotos_client_id": str(existing_mid.client_id),
                "gphotos_media_item_id": f"gphotos_{existing_mid.object_id}",
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "width": 100,
                "height": 200,
                "date_taken": MOCK_DATE_TAKEN,
            }
        )

        with self.assertRaisesRegex(
            ValueError, "Unable to delete all media items in .*"
        ):
            self.repo.delete_many_media_items(ids_to_delete)
