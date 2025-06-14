from typing import Dict, cast
import unittest
from bson.objectid import ObjectId

from photos_drive.shared.metadata.mongodb.albums_repository_impl import (
    AlbumsRepositoryImpl,
)
from photos_drive.shared.metadata.albums_repository import (
    AlbumsRepository,
    UpdateAlbumRequest,
    UpdatedAlbumFields,
)
from photos_drive.shared.metadata.album_id import AlbumId
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.mongodb.testing import (
    create_mock_mongo_client,
)

MONGO_CLIENT_ID = ObjectId("5f50c31e8a7d4b1c9c9b0b1a")


class TestAlbumsRepositoryImpl(unittest.TestCase):

    def setUp(self):
        self.mock_client = create_mock_mongo_client()
        self.mongo_clients_repo = MongoDbClientsRepository()
        self.mongo_clients_repo.add_mongodb_client(MONGO_CLIENT_ID, self.mock_client)
        self.repo: AlbumsRepository = AlbumsRepositoryImpl(self.mongo_clients_repo)

    def test_get_album_by_id(self):
        # Prepare test data
        album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        self.mock_client["sharded_google_photos"]["albums"].insert_one(
            {
                "_id": album_id.object_id,
                "name": "Test Album",
                "parent_album_id": '5f50c31e8a7d4b1c9c9b0b1c:5f50c31e8a7d4b1c9c9b0b1d',
                "child_album_ids": [
                    "5f50c31e8a7d4b1c9c9b0b1e:5f50c31e8a7d4b1c9c9b0b1f"
                ],
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

    def test_get_all_albums(self):
        # Arrange: Prepare test data
        album_id_1 = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        album_id_2 = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1c"))
        self.mock_client["sharded_google_photos"]["albums"].insert_one(
            {
                "_id": album_id_1.object_id,
                "name": "Archives",
                "parent_album_id": None,
                "child_album_ids": [
                    "5f50c31e8a7d4b1c9c9b0b1a:5f50c31e8a7d4b1c9c9b0b1c"
                ],
            }
        )
        self.mock_client["sharded_google_photos"]["albums"].insert_one(
            {
                "_id": album_id_2.object_id,
                "name": "Photos",
                "parent_album_id": f"5f50c31e8a7d4b1c9c9b0b1a:{album_id_1.object_id}",
                "child_album_ids": [],
            }
        )

        # Act: get all albums
        albums = self.repo.get_all_albums()

        # Assert: check all albums
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].name, "Archives")
        self.assertEqual(albums[0].id, album_id_1)
        self.assertEqual(albums[0].parent_album_id, None)
        self.assertEqual(albums[0].child_album_ids, [album_id_2])

        self.assertEqual(albums[1].name, "Photos")
        self.assertEqual(albums[1].id, album_id_2)
        self.assertEqual(albums[1].parent_album_id, album_id_1)
        self.assertEqual(albums[1].child_album_ids, [])

    def test_get_album_by_id__unknown_album_id(self):
        album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))

        with self.assertRaisesRegex(ValueError, "Album .* does not exist!"):
            self.repo.get_album_by_id(album_id)

    def test_create_album(self):
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

        # Test
        album = self.repo.create_album(album_name, parent_album_id, child_album_ids)

        # Assert
        self.assertEqual(album.name, album_name)
        self.assertEqual(album.parent_album_id, parent_album_id)
        self.assertEqual(album.child_album_ids, child_album_ids)

        # Check if the album was actually inserted into the mock database
        inserted_album = self.mock_client["sharded_google_photos"]["albums"].find_one(
            {"_id": album.id.object_id}
        )
        self.assertIsNotNone(inserted_album)

    def test_delete_many_albums__deletes_multiple_albums_successfully(self):
        # Prepare test data
        album_ids = [
            AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b")),
            AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1c")),
            AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1d")),
        ]

        for album_id in album_ids:
            self.mock_client["sharded_google_photos"]["albums"].insert_one(
                {
                    "_id": album_id.object_id,
                    "name": f"Test Album {album_id.object_id}",
                    "parent_album_id": None,
                    "child_album_ids": [],
                }
            )

        # Test
        self.repo.delete_many_albums(album_ids)

        # Assert
        for album_id in album_ids:
            self.assertIsNone(
                self.mock_client["sharded_google_photos"]["albums"].find_one(
                    {"_id": album_id.object_id}
                )
            )

    def test_delete_many_albums__with_non_existent_albums__raises_value_error(self):
        # Prepare test data
        existing_album_id = AlbumId(
            MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        )
        non_existent_album_id = AlbumId(
            MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1c")
        )

        self.mock_client["sharded_google_photos"]["albums"].insert_one(
            {
                "_id": existing_album_id.object_id,
                "name": "Existing Album",
                "parent_album_id": None,
                "child_album_ids": [],
            }
        )

        # Test
        with self.assertRaises(ValueError):
            self.repo.delete_many_albums([existing_album_id, non_existent_album_id])

    def test_delete_many_albums__with_albums_from_different_clients(self):
        # Prepare test data
        mongo_client_id_2 = ObjectId("5f50c31e8a7d4b1c9c9b0b1c")
        album_id_1 = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        album_id_2 = AlbumId(mongo_client_id_2, ObjectId("5f50c31e8a7d4b1c9c9b0b1d"))
        mock_client_2 = create_mock_mongo_client()
        self.mongo_clients_repo.add_mongodb_client(mongo_client_id_2, mock_client_2)
        self.mock_client["sharded_google_photos"]["albums"].insert_one(
            {
                "_id": album_id_1.object_id,
                "name": "Album 1",
                "parent_album_id": None,
                "child_album_ids": [],
            }
        )
        mock_client_2["sharded_google_photos"]["albums"].insert_one(
            {
                "_id": album_id_2.object_id,
                "name": "Album 2",
                "parent_album_id": None,
                "child_album_ids": [],
            }
        )

        # Test
        self.repo.delete_many_albums([album_id_1, album_id_2])

        # Assert
        self.assertIsNone(
            self.mock_client["sharded_google_photos"]["albums"].find_one(
                {"_id": album_id_1.object_id}
            )
        )
        self.assertIsNone(
            mock_client_2["sharded_google_photos"]["albums"].find_one(
                {"_id": album_id_2.object_id}
            )
        )

    def test_delete_album__with_valid_id(self):
        # Prepare test data
        album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
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

    def test_delete_album__with_unknown_id(self):
        album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))

        with self.assertRaisesRegex(
            ValueError, 'Unable to delete album: Album .* not found'
        ):
            self.repo.delete_album(album_id)

    def test_update_album__with_new_fields(self):
        # Prepare test data
        album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        self.mock_client["sharded_google_photos"]["albums"].insert_one(
            {
                "_id": album_id.object_id,
                "name": "Old Name",
                "parent_album_id": "5f50c31e8a7d4b1c9c9b0b1c:5f50c31e8a7d4b1c9c9b0b1d",
                "child_album_ids": [],
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

    def test_update_album__with_unknown_album_id__throws_error(self):
        album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        updated_fields = UpdatedAlbumFields(
            new_name="New Name",
            new_parent_album_id=AlbumId(ObjectId(), ObjectId()),
            new_child_album_ids=[AlbumId(ObjectId(), ObjectId())],
        )

        with self.assertRaisesRegex(ValueError, "Unable to update album .*"):
            self.repo.update_album(album_id, updated_fields)

    def test_update_albums__with_new_fields(self):
        album_2010 = self.repo.create_album('2010', None, [])
        album_2011 = self.repo.create_album('2011', None, [])
        album_2012 = self.repo.create_album('2012', None, [])
        album_2013 = self.repo.create_album('2013', None, [])
        photo_album = self.repo.create_album('Photos', None, [])

        requests = [
            UpdateAlbumRequest(album_2010.id, new_parent_album_id=photo_album.id),
            UpdateAlbumRequest(album_2011.id, new_parent_album_id=photo_album.id),
            UpdateAlbumRequest(album_2012.id, new_parent_album_id=photo_album.id),
            UpdateAlbumRequest(album_2013.id, new_parent_album_id=photo_album.id),
        ]
        self.repo.update_many_albums(requests)

        self.assertEqual(
            self.repo.get_album_by_id(album_2010.id).parent_album_id, photo_album.id
        )
        self.assertEqual(
            self.repo.get_album_by_id(album_2011.id).parent_album_id, photo_album.id
        )
        self.assertEqual(
            self.repo.get_album_by_id(album_2012.id).parent_album_id, photo_album.id
        )
        self.assertEqual(
            self.repo.get_album_by_id(album_2013.id).parent_album_id, photo_album.id
        )
