from datetime import datetime
import os
import unittest

from bson import Binary
from bson.objectid import ObjectId

from photos_drive.shared.core.albums.album_id import (
    AlbumId,
    album_id_to_string,
)
from photos_drive.shared.core.databases.mongodb import (
    MongoDBClientsRepository,
)
from photos_drive.shared.core.media_items.gps_location import (
    GpsLocation,
)
from photos_drive.shared.core.media_items.media_item_id import MediaItemId
from photos_drive.shared.core.media_items.repository.base import (
    CreateMediaItemRequest,
    FindMediaItemRequest,
    UpdateMediaItemRequest,
)
from photos_drive.shared.core.media_items.repository.mongodb import (
    MongoDBMediaItemsRepository,
)
from photos_drive.shared.core.testing import (
    create_mock_mongo_client,
)
from photos_drive.shared.features.llm.vector_stores.base_vector_store import (
    MediaItemEmbeddingId,
    embedding_id_to_string,
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

MOCK_EMBEDDING_ID_1 = MediaItemEmbeddingId(ObjectId(), ObjectId())

MOCK_EMBEDDING_ID_2 = MediaItemEmbeddingId(ObjectId(), ObjectId())


class TestMediaItemsRepositoryImpl(unittest.TestCase):

    def setUp(self):
        self.mongodb_client_id = ObjectId()
        self.mongodb_client = create_mock_mongo_client()
        self.mongodb_clients_repo = MongoDBClientsRepository()
        self.mongodb_clients_repo.add_mongodb_client(
            self.mongodb_client_id, self.mongodb_client
        )
        self.repo = MongoDBMediaItemsRepository(
            self.mongodb_client_id, self.mongodb_client, self.mongodb_clients_repo
        )

    def test_get_media_item_by_id(self):
        fake_file_hash = os.urandom(16)
        media_item_id = MediaItemId(self.mongodb_client_id, ObjectId())

        # Insert a mock media item into the mock database
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "embedding_id": embedding_id_to_string(MOCK_EMBEDDING_ID_1),
                "mime_type": "image/jpeg",
            }
        )

        # Test retrieval
        media_item = self.repo.get_media_item_by_id(media_item_id)

        # Assert the retrieved media item matches the inserted data
        self.assertEqual(media_item.file_name, "test_image.jpg")
        self.assertEqual(media_item.file_hash, fake_file_hash)
        self.assertEqual(media_item.location, GpsLocation(56.78, 12.34))
        self.assertEqual(media_item.gphotos_client_id, media_item_id.client_id)
        self.assertEqual(media_item.gphotos_media_item_id, "gphotos_123")
        self.assertEqual(media_item.width, 100)
        self.assertEqual(media_item.height, 200)
        self.assertEqual(media_item.date_taken, MOCK_DATE_TAKEN)
        self.assertEqual(media_item.embedding_id, MOCK_EMBEDDING_ID_1)
        self.assertEqual(media_item.mime_type, "image/jpeg")

    def test_get_media_item_by_id_not_found(self):
        media_item_id = MediaItemId(self.mongodb_client_id, ObjectId())

        with self.assertRaisesRegex(ValueError, "Media item .* does not exist!"):
            self.repo.get_media_item_by_id(media_item_id)

    def test_get_media_item_by_id_wrong_client_id(self):
        media_item_id = MediaItemId(ObjectId(), ObjectId())

        with self.assertRaisesRegex(
            ValueError, "Media item .* belongs to a different client"
        ):
            self.repo.get_media_item_by_id(media_item_id)

    def test_get_all_media_items(self):
        fake_file_hash = os.urandom(16)

        # Insert a mock media item into the mock database
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "embedding_id": embedding_id_to_string(MOCK_EMBEDDING_ID_1),
                "mime_type": "image/jpeg",
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
        self.assertEqual(media_items[0].embedding_id, MOCK_EMBEDDING_ID_1)
        self.assertEqual(media_items[0].mime_type, "image/jpeg")

    def test_get_all_media_items_with_no_date_taken_and_no_embedding_id_and_no_location(
        self,
    ):
        fake_file_hash = os.urandom(16)

        # Insert a mock media item into the mock database
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
            {
                "file_name": "test_image.jpg",
                "file_hash": Binary(fake_file_hash),
                "gphotos_client_id": str(self.mongodb_client_id),
                "gphotos_media_item_id": "gphotos_123",
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "width": 100,
                "height": 200,
                "mime_type": "image/jpeg",
            }
        )

        # Test retrieval
        media_items = self.repo.get_all_media_items()

        # Assert the retrieved media item matches the inserted data
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].file_name, "test_image.jpg")
        self.assertEqual(media_items[0].file_hash, fake_file_hash)
        self.assertIsNone(media_items[0].location)
        self.assertEqual(media_items[0].gphotos_client_id, self.mongodb_client_id)
        self.assertEqual(media_items[0].gphotos_media_item_id, "gphotos_123")
        self.assertEqual(media_items[0].width, 100)
        self.assertEqual(media_items[0].height, 200)
        self.assertEqual(media_items[0].date_taken, datetime(1970, 1, 1))
        self.assertIsNone(media_items[0].embedding_id)
        self.assertEqual(media_items[0].mime_type, "image/jpeg")

    def test_find_media_items(self):
        # Insert mock media items from different albums into the mock database
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "embedding_id": embedding_id_to_string(MOCK_EMBEDDING_ID_1),
                "mime_type": "image/jpeg",
            }
        )
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "embedding_id": embedding_id_to_string(MOCK_EMBEDDING_ID_1),
                "mime_type": "image/jpeg",
            }
        )
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "embedding_id": embedding_id_to_string(MOCK_EMBEDDING_ID_1),
                "mime_type": "image/jpeg",
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
        self.assertEqual(media_items[0].embedding_id, MOCK_EMBEDDING_ID_1)
        self.assertEqual(media_items[0].mime_type, 'image/jpeg')

    def test_find_media_items_excluded_by_client_id(self):
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
            {
                "file_name": "test_image.jpg",
                "gphotos_client_id": str(self.mongodb_client_id),
                "album_id": album_id_to_string(MOCK_ALBUM_ID),
                "file_hash": Binary(os.urandom(16)),
                "mime_type": "image/jpeg",
            }
        )

        media_items = self.repo.find_media_items(
            FindMediaItemRequest(mongodb_client_ids=[ObjectId()])
        )

        self.assertEqual(len(media_items), 0)

    def test_get_num_media_items_in_album(self):
        # Insert mock media items from different albums into the mock database
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "embedding_id": embedding_id_to_string(MOCK_EMBEDDING_ID_1),
                "mime_type": "image/jpeg",
            }
        )
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "embedding_id": embedding_id_to_string(MOCK_EMBEDDING_ID_1),
                "mime_type": "image/jpeg",
            }
        )
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "embedding_id": embedding_id_to_string(MOCK_EMBEDDING_ID_1),
                "mime_type": "image/jpeg",
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
            embedding_id=MOCK_EMBEDDING_ID_1,
            mime_type="image/jpeg",
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
        self.assertEqual(media_item.embedding_id, MOCK_EMBEDDING_ID_1)
        self.assertEqual(media_item.mime_type, "image/jpeg")

    def test_create_media_item_with_no_embedding_id_no_location(self):
        fake_file_hash = os.urandom(16)
        request = CreateMediaItemRequest(
            file_name="new_image.jpg",
            file_hash=fake_file_hash,
            location=None,
            gphotos_client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
            gphotos_media_item_id="gphotos_456",
            album_id=MOCK_ALBUM_ID,
            width=100,
            height=200,
            date_taken=MOCK_DATE_TAKEN,
            embedding_id=None,
            mime_type="image/png",
        )

        # Test creation of media item
        media_item = self.repo.create_media_item(request)

        # Assert that the media item was created correctly
        self.assertEqual(media_item.id.client_id, self.mongodb_client_id)
        self.assertEqual(media_item.file_name, "new_image.jpg")
        self.assertEqual(media_item.file_hash, fake_file_hash)
        self.assertIsNone(media_item.location)
        self.assertEqual(media_item.gphotos_client_id, request.gphotos_client_id)
        self.assertEqual(
            media_item.gphotos_media_item_id, request.gphotos_media_item_id
        )
        self.assertEqual(media_item.width, 100)
        self.assertEqual(media_item.height, 200)
        self.assertEqual(media_item.date_taken, MOCK_DATE_TAKEN)
        self.assertIsNone(media_item.embedding_id)
        self.assertEqual(media_item.mime_type, "image/png")

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
                embedding_id=MOCK_EMBEDDING_ID_1,
                mime_type="image/jpeg",
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
                embedding_id=MOCK_EMBEDDING_ID_1,
                mime_type="image/jpeg",
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
                    clear_embedding_id=False,
                    new_embedding_id=MOCK_EMBEDDING_ID_2,
                    new_mime_type="image/png",
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
                    clear_embedding_id=False,
                    new_embedding_id=MOCK_EMBEDDING_ID_2,
                    new_mime_type="image/png",
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
        self.assertEqual(new_media_item_1.embedding_id, MOCK_EMBEDDING_ID_2)
        self.assertEqual(new_media_item_1.mime_type, "image/png")

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
        self.assertEqual(new_media_item_2.embedding_id, MOCK_EMBEDDING_ID_2)
        self.assertEqual(new_media_item_2.mime_type, "image/png")

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
                embedding_id=None,
                mime_type="image/jpeg",
            )
        )

        self.repo.update_many_media_items(
            [UpdateMediaItemRequest(media_item_id=media_item_1.id, clear_location=True)]
        )

        new_media_item_1 = self.repo.get_media_item_by_id(media_item_1.id)
        self.assertIsNone(new_media_item_1.location)

    def test_update_many_media_items_clear_embedding_id(self):
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
                embedding_id=MOCK_EMBEDDING_ID_1,
                mime_type="image/jpeg",
            )
        )

        self.repo.update_many_media_items(
            [
                UpdateMediaItemRequest(
                    media_item_id=media_item_1.id, clear_embedding_id=True
                )
            ]
        )

        new_media_item_1 = self.repo.get_media_item_by_id(media_item_1.id)
        self.assertIsNone(new_media_item_1.embedding_id)

    def test_update_many_media_items_on_unknown_media_item_id(self):
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
                embedding_id=None,
                mime_type="image/jpeg",
            )
        )

        with self.assertRaisesRegex(
            ValueError, "Unable to update all media items: 0 vs 1"
        ):
            self.repo.update_many_media_items(
                [
                    UpdateMediaItemRequest(
                        MediaItemId(
                            media_item_1.id.client_id,
                            ObjectId('5f50c31e8a7d4b1c9c9b0b12'),
                        )
                    )
                ]
            )

    def test_delete_media_item(self):
        # Insert a mock media item into the mock database
        media_item_id = MediaItemId(self.mongodb_client_id, ObjectId())
        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "mime_type": "image/jpeg",
            }
        )

        # Test deletion
        self.repo.delete_media_item(media_item_id)

        # Assert that the media item has been deleted
        deleted_media = self.mongodb_client["photos_drive"]["media_items"].find_one(
            {"_id": media_item_id.object_id}
        )
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
            self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                    "mime_type": "image/jpeg",
                }
            )

        # Test deletion of multiple items
        self.repo.delete_many_media_items(ids_to_delete)

        # Assert that all items have been deleted
        for mid in ids_to_delete:
            deleted_media = self.mongodb_client["photos_drive"]["media_items"].find_one(
                {"_id": mid.object_id}
            )
            self.assertIsNone(deleted_media)

    def test_delete_many_media_items_with_no_documents_throws_no_errors(self):
        self.repo.delete_many_media_items([])

    def test_delete_many_media_items_partial_failure(self):
        ids_to_delete = [
            MediaItemId(self.mongodb_client_id, ObjectId()),
            MediaItemId(self.mongodb_client_id, ObjectId()),
        ]

        # Insert one mock item into the database but not the other
        existing_mid = ids_to_delete[0]

        self.mongodb_client["photos_drive"]["media_items"].insert_one(
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
                "mime_type": "image/jpeg",
            }
        )

        with self.assertRaisesRegex(
            ValueError, "Unable to delete all media items in .*"
        ):
            self.repo.delete_many_media_items(ids_to_delete)

    def test_get_client_id(self):
        self.assertEqual(self.repo.get_client_id(), self.mongodb_client_id)

    def test_get_available_free_space(self):
        self.assertGreater(self.repo.get_available_free_space(), 0)

    def test_update_many_media_items_wrong_client_id(self):
        with self.assertRaisesRegex(
            ValueError, "Media item .* belongs to a different client"
        ):
            self.repo.update_many_media_items(
                [
                    UpdateMediaItemRequest(
                        media_item_id=MediaItemId(ObjectId(), ObjectId())
                    )
                ]
            )

    def test_delete_media_item_wrong_client_id(self):
        with self.assertRaisesRegex(
            ValueError, "Media item .* belongs to a different client"
        ):
            self.repo.delete_media_item(MediaItemId(ObjectId(), ObjectId()))

    def test_delete_many_media_items_wrong_client_id(self):
        with self.assertRaisesRegex(
            ValueError, "Media item .* belongs to a different client"
        ):
            self.repo.delete_many_media_items([MediaItemId(ObjectId(), ObjectId())])
