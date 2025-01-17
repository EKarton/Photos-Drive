from typing import Dict, cast
import unittest
from unittest.mock import Mock
from bson.objectid import ObjectId
import mongomock

from sharded_photos_drive_cli_client.shared.mongodb.albums_repository import (
    AlbumsRepository,
    AlbumsRepositoryImpl,
    UpdatedAlbumFields,
)
from sharded_photos_drive_cli_client.shared.mongodb.albums import AlbumId
from sharded_photos_drive_cli_client.shared.mongodb.media_items import MediaItemId
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
)


class TestAlbumsRepositoryImpl(unittest.TestCase):

    def setUp(self):
        self.mock_client = mongomock.MongoClient()
        self.mock_clients_repo = Mock(spec=MongoDbClientsRepository)
        self.mock_clients_repo.get_client_by_id.return_value = self.mock_client
        self.mock_clients_repo.find_id_of_client_with_most_space.return_value = (
            ObjectId("5f50c31e8a7d4b1c9c9b0b1a")
        )
        self.repo: AlbumsRepository = AlbumsRepositoryImpl(self.mock_clients_repo)

    def test_get_album_by_id__finds_and_returns_album_correctly(self):
        # Prepare test data
        album_id = AlbumId(
            ObjectId("5f50c31e8a7d4b1c9c9b0b1a"), ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        )
        self.mock_client["sharded_google_photos"]["albums"].insert_one(
            {
                "_id": album_id.object_id,
                "name": "Test Album",
                "parent_album_id": "5f50c31e8a7d4b1c9c9b0b1c:5f50c31e8a7d4b1c9c9b0b1d",
                "child_album_ids": [
                    "5f50c31e8a7d4b1c9c9b0b1e:5f50c31e8a7d4b1c9c9b0b1f"
                ],
                "media_item_ids": ["5f50c31e8a7d4b1c9c9b0b20:5f50c31e8a7d4b1c9c9b0b21"],
            }
        )

        # Test
        album = self.repo.get_album_by_id(album_id)

        # Assert
        self.assertEqual(album.id, album_id)
        self.assertEqual(album.name, "Test Album")
        self.assertEqual(
            album.parent_album_id,
            AlbumId(
                ObjectId("5f50c31e8a7d4b1c9c9b0b1c"),
                ObjectId("5f50c31e8a7d4b1c9c9b0b1d"),
            ),
        )
        self.assertEqual(
            album.child_album_ids,
            [
                AlbumId(
                    ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
                    ObjectId("5f50c31e8a7d4b1c9c9b0b1f"),
                )
            ],
        )
        self.assertEqual(
            album.media_item_ids,
            [
                MediaItemId(
                    ObjectId("5f50c31e8a7d4b1c9c9b0b20"),
                    ObjectId("5f50c31e8a7d4b1c9c9b0b21"),
                )
            ],
        )

    def test_get_album_by_id__unknown_album_id__throws_error(self):
        album_id = AlbumId(
            ObjectId("5f50c31e8a7d4b1c9c9b0b1a"), ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        )

        with self.assertRaisesRegex(ValueError, "Album .* does not exist!"):
            self.repo.get_album_by_id(album_id)

    def test_create_album__creates_album_in_database_and_returns_album_instance(self):
        # Prepare test data
        album_name = "New Album"
        parent_album_id = AlbumId(
            ObjectId("5f50c31e8a7d4b1c9c9b0b1c"), ObjectId("5f50c31e8a7d4b1c9c9b0b1d")
        )
        child_album_ids = [
            AlbumId(
                ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
                ObjectId("5f50c31e8a7d4b1c9c9b0b1f"),
            )
        ]
        media_item_ids = [
            MediaItemId(
                ObjectId("5f50c31e8a7d4b1c9c9b0b20"),
                ObjectId("5f50c31e8a7d4b1c9c9b0b21"),
            )
        ]

        # Test
        album = self.repo.create_album(
            album_name, parent_album_id, child_album_ids, media_item_ids
        )

        # Assert
        self.assertEqual(album.name, album_name)
        self.assertEqual(album.parent_album_id, parent_album_id)
        self.assertEqual(album.child_album_ids, child_album_ids)
        self.assertEqual(album.media_item_ids, media_item_ids)

        # Check if the album was actually inserted into the mock database
        inserted_album = self.mock_client["sharded_google_photos"]["albums"].find_one(
            {"_id": album.id.object_id}
        )
        self.assertIsNotNone(inserted_album)

    def test_delete_album__with_valid_id__deletes_album_from_database(self):
        # Prepare test data
        album_id = AlbumId(
            ObjectId("5f50c31e8a7d4b1c9c9b0b1a"), ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        )
        self.mock_client["sharded_google_photos"]["albums"].insert_one(
            {"_id": album_id.object_id, "name": "Test Album"}
        )

        # Test
        self.repo.delete_album(album_id)

        # Assert
        deleted_album = self.mock_client["sharded_google_photos"]["albums"].find_one(
            {"_id": album_id.object_id}
        )
        self.assertIsNone(deleted_album)

    def test_delete_album__with_unknown_id__throws_error(self):
        album_id = AlbumId(
            ObjectId("5f50c31e8a7d4b1c9c9b0b1a"), ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        )

        with self.assertRaisesRegex(
            ValueError, 'Unable to delete album: Album .* not found'
        ):
            self.repo.delete_album(album_id)

    def test_update_album__with_new_fields__updates_album_and_returns_new_album_instance(
        self,
    ):
        # Prepare test data
        album_id = AlbumId(
            ObjectId("5f50c31e8a7d4b1c9c9b0b1a"), ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        )
        self.mock_client["sharded_google_photos"]["albums"].insert_one(
            {
                "_id": album_id.object_id,
                "name": "Old Name",
                "parent_album_id": "5f50c31e8a7d4b1c9c9b0b1c:5f50c31e8a7d4b1c9c9b0b1d",
                "child_album_ids": [],
                "media_item_ids": [],
            }
        )
        updated_fields = UpdatedAlbumFields(
            new_name="New Name",
            new_parent_album_id=AlbumId(
                ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
                ObjectId("5f50c31e8a7d4b1c9c9b0b1f"),
            ),
            new_child_album_ids=[
                AlbumId(
                    ObjectId("5f50c31e8a7d4b1c9c9b0b20"),
                    ObjectId("5f50c31e8a7d4b1c9c9b0b21"),
                )
            ],
            new_media_item_ids=[
                MediaItemId(
                    ObjectId("5f50c31e8a7d4b1c9c9b0b22"),
                    ObjectId("5f50c31e8a7d4b1c9c9b0b23"),
                )
            ],
        )

        # Test
        self.repo.update_album(album_id, updated_fields)

        # Assert
        updated_album = cast(
            Dict,
            self.mock_client["sharded_google_photos"]["albums"].find_one(
                {"_id": album_id.object_id}
            ),
        )
        self.assertEqual(updated_album["name"], "New Name")
        self.assertEqual(
            updated_album["parent_album_id"],
            "5f50c31e8a7d4b1c9c9b0b1e:5f50c31e8a7d4b1c9c9b0b1f",
        )
        self.assertEqual(
            updated_album["child_album_ids"],
            ["5f50c31e8a7d4b1c9c9b0b20:5f50c31e8a7d4b1c9c9b0b21"],
        )
        self.assertEqual(
            updated_album["media_item_ids"],
            ["5f50c31e8a7d4b1c9c9b0b22:5f50c31e8a7d4b1c9c9b0b23"],
        )

    def test_update_album__with_unknown_album_id__throws_error(self):
        album_id = AlbumId(
            ObjectId("5f50c31e8a7d4b1c9c9b0b1a"), ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        )
        updated_fields = UpdatedAlbumFields(
            new_name="New Name",
            new_parent_album_id=AlbumId(ObjectId(), ObjectId()),
            new_child_album_ids=[AlbumId(ObjectId(), ObjectId())],
            new_media_item_ids=[MediaItemId(ObjectId(), ObjectId())],
        )

        # Test
        with self.assertRaisesRegex(ValueError, "Unable to update album .*"):
            self.repo.update_album(album_id, updated_fields)
