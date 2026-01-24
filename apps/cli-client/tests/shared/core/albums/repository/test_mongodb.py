from typing import Dict, cast
import unittest

from bson.objectid import ObjectId

from photos_drive.shared.core.albums.album_id import AlbumId, album_id_to_string
from photos_drive.shared.core.albums.repository.base import (
    AlbumsRepository,
    UpdateAlbumRequest,
    UpdatedAlbumFields,
)
from photos_drive.shared.core.albums.repository.mongodb import (
    MongoDBAlbumsRepository,
)
from photos_drive.shared.core.clients.mongodb import (
    MongoDbTransactionRepository,
)
from photos_drive.shared.core.testing import (
    create_mock_mongo_client,
)

MONGO_CLIENT_ID = ObjectId("5f50c31e8a7d4b1c9c9b0b1a")


class TestAlbumsRepositoryImpl(unittest.TestCase):

    def setUp(self):
        self.mock_client = create_mock_mongo_client()
        self.mongo_clients_repo = MongoDbTransactionRepository()
        self.mongo_clients_repo.add_mongodb_client(MONGO_CLIENT_ID, self.mock_client)
        self.repo: AlbumsRepository = MongoDBAlbumsRepository(
            MONGO_CLIENT_ID, self.mock_client, self.mongo_clients_repo
        )

    def test_get_album_by_id(self):
        # Prepare test data
        album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        self.mock_client["photos_drive"]["albums"].insert_one(
            {
                "_id": album_id.object_id,
                "name": "Test Album",
                "parent_album_id": '5f50c31e8a7d4b1c9c9b0b1c:5f50c31e8a7d4b1c9c9b0b1d',
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

    def test_get_all_albums(self):
        # Arrange: Prepare test data
        album_id_1 = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        album_id_2 = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1c"))
        self.mock_client["photos_drive"]["albums"].insert_one(
            {
                "_id": album_id_1.object_id,
                "name": "Archives",
                "parent_album_id": None,
            }
        )
        self.mock_client["photos_drive"]["albums"].insert_one(
            {
                "_id": album_id_2.object_id,
                "name": "Photos",
                "parent_album_id": f"5f50c31e8a7d4b1c9c9b0b1a:{album_id_1.object_id}",
            }
        )

        # Act: get all albums
        albums = self.repo.get_all_albums()

        # Assert: check all albums
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].name, "Archives")
        self.assertEqual(albums[0].id, album_id_1)
        self.assertEqual(albums[0].parent_album_id, None)

        self.assertEqual(albums[1].name, "Photos")
        self.assertEqual(albums[1].id, album_id_2)
        self.assertEqual(albums[1].parent_album_id, album_id_1)

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

        # Test
        album = self.repo.create_album(album_name, parent_album_id)

        # Assert
        self.assertEqual(album.name, album_name)
        self.assertEqual(album.parent_album_id, parent_album_id)

        # Check if the album was actually inserted into the mock database
        inserted_album = self.mock_client["photos_drive"]["albums"].find_one(
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
            self.mock_client["photos_drive"]["albums"].insert_one(
                {
                    "_id": album_id.object_id,
                    "name": f"Test Album {album_id.object_id}",
                    "parent_album_id": None,
                }
            )

        # Test
        self.repo.delete_many_albums(album_ids)

        # Assert
        for album_id in album_ids:
            self.assertIsNone(
                self.mock_client["photos_drive"]["albums"].find_one(
                    {"_id": album_id.object_id}
                )
            )

    def test_delete_many_albums_with_no_albums_does_not_throw_error(self):
        self.repo.delete_many_albums([])

    def test_delete_many_albums__with_non_existent_albums__raises_value_error(self):
        # Prepare test data
        existing_album_id = AlbumId(
            MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        )
        non_existent_album_id = AlbumId(
            MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1c")
        )

        self.mock_client["photos_drive"]["albums"].insert_one(
            {
                "_id": existing_album_id.object_id,
                "name": "Existing Album",
                "parent_album_id": None,
            }
        )

        # Test
        with self.assertRaises(ValueError):
            self.repo.delete_many_albums([existing_album_id, non_existent_album_id])

    def test_delete_album__with_valid_id(self):
        # Prepare test data
        album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        self.mock_client["photos_drive"]["albums"].insert_one(
            {"_id": album_id.object_id, "name": "Test Album"}
        )

        # Test
        self.repo.delete_album(album_id)

        # Assert
        deleted_album = self.mock_client["photos_drive"]["albums"].find_one(
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
        self.mock_client["photos_drive"]["albums"].insert_one(
            {
                "_id": album_id.object_id,
                "name": "Old Name",
                "parent_album_id": "5f50c31e8a7d4b1c9c9b0b1c:5f50c31e8a7d4b1c9c9b0b1d",
            }
        )
        updated_fields = UpdatedAlbumFields(
            new_name="New Name",
            new_parent_album_id=AlbumId(
                ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
                ObjectId("5f50c31e8a7d4b1c9c9b0b1f"),
            ),
        )

        # Test
        self.repo.update_album(album_id, updated_fields)

        # Assert
        updated_album = cast(
            Dict,
            self.mock_client["photos_drive"]["albums"].find_one(
                {"_id": album_id.object_id}
            ),
        )
        self.assertEqual(updated_album["name"], "New Name")
        self.assertEqual(
            updated_album["parent_album_id"],
            "5f50c31e8a7d4b1c9c9b0b1e:5f50c31e8a7d4b1c9c9b0b1f",
        )

    def test_update_album__with_unknown_album_id__throws_error(self):
        album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        updated_fields = UpdatedAlbumFields(
            new_name="New Name",
            new_parent_album_id=AlbumId(ObjectId(), ObjectId()),
        )

        with self.assertRaisesRegex(ValueError, "Unable to update album .*"):
            self.repo.update_album(album_id, updated_fields)

    def test_update_many_albums(self):
        album_2010 = self.repo.create_album('2010', None)
        album_2011 = self.repo.create_album('2011', None)
        album_2012 = self.repo.create_album('2012', None)
        album_2013 = self.repo.create_album('2013', None)
        photo_album = self.repo.create_album('Photos', None)

        requests = [
            UpdateAlbumRequest(
                album_2010.id, new_name="1910", new_parent_album_id=photo_album.id
            ),
            UpdateAlbumRequest(
                album_2011.id, new_name="1911", new_parent_album_id=photo_album.id
            ),
            UpdateAlbumRequest(
                album_2012.id, new_name="1912", new_parent_album_id=photo_album.id
            ),
            UpdateAlbumRequest(
                album_2013.id, new_name="1913", new_parent_album_id=photo_album.id
            ),
        ]
        self.repo.update_many_albums(requests)

        new_album_2010 = self.repo.get_album_by_id(album_2010.id)
        self.assertEqual(new_album_2010.name, '1910')
        self.assertEqual(new_album_2010.parent_album_id, photo_album.id)

        new_album_2011 = self.repo.get_album_by_id(album_2011.id)
        self.assertEqual(new_album_2011.name, '1911')
        self.assertEqual(new_album_2011.parent_album_id, photo_album.id)

        new_album_2012 = self.repo.get_album_by_id(album_2012.id)
        self.assertEqual(new_album_2012.name, '1912')
        self.assertEqual(new_album_2012.parent_album_id, photo_album.id)

        new_album_2013 = self.repo.get_album_by_id(album_2013.id)
        self.assertEqual(new_album_2013.name, '1913')
        self.assertEqual(new_album_2013.parent_album_id, photo_album.id)

    def test_update_many_albums_on_unknown_albums(self):
        requests = [
            UpdateAlbumRequest(
                AlbumId(MONGO_CLIENT_ID, ObjectId()),
                new_name="1910",
            ),
        ]

        with self.assertRaisesRegex(ValueError, "Unable to update all albums: 0 vs 1"):
            self.repo.update_many_albums(requests)

    def test_find_child_albums(self):
        parent_album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1a"))
        child_album_id_1 = AlbumId(
            MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        )
        child_album_id_2 = AlbumId(
            MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1c")
        )

        self.mock_client["photos_drive"]["albums"].insert_many(
            [
                {
                    "_id": parent_album_id.object_id,
                    "name": "Parent Album",
                    "parent_album_id": None,
                },
                {
                    "_id": child_album_id_1.object_id,
                    "name": "Child 1",
                    "parent_album_id": album_id_to_string(parent_album_id),
                },
                {
                    "_id": child_album_id_2.object_id,
                    "name": "Child 2",
                    "parent_album_id": album_id_to_string(parent_album_id),
                },
            ]
        )

        children = self.repo.find_child_albums(parent_album_id)

        self.assertEqual(len(children), 2)
        self.assertCountEqual(
            [child.id for child in children],
            [child_album_id_1, child_album_id_2],
        )
        self.assertTrue(
            all(child.parent_album_id == parent_album_id for child in children)
        )

    def test_count_child_albums(self):
        parent_album_id = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1a"))
        self.mock_client["photos_drive"]["albums"].insert_many(
            [
                {
                    "_id": ObjectId(),
                    "name": "Child 1",
                    "parent_album_id": album_id_to_string(parent_album_id),
                },
                {
                    "_id": ObjectId(),
                    "name": "Child 2",
                    "parent_album_id": album_id_to_string(parent_album_id),
                },
                {
                    "_id": ObjectId(),
                    "name": "Unrelated",
                    "parent_album_id": None,
                },
            ]
        )

        count = self.repo.count_child_albums(parent_album_id)

        self.assertEqual(count, 2)
