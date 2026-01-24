import unittest
from unittest.mock import Mock

from bson.objectid import ObjectId

from photos_drive.shared.core.albums.album_id import AlbumId
from photos_drive.shared.core.albums.albums import Album
from photos_drive.shared.core.albums.repository.base import (
    AlbumsRepository,
    UpdateAlbumRequest,
    UpdatedAlbumFields,
)
from photos_drive.shared.core.albums.repository.union import (
    UnionAlbumsRepository,
)


class TestUnionAlbumsRepository(unittest.TestCase):
    def setUp(self):
        self.mock_repo_1 = Mock(spec=AlbumsRepository)
        self.mock_repo_2 = Mock(spec=AlbumsRepository)

        self.client_id_1 = ObjectId()
        self.client_id_2 = ObjectId()

        self.mock_repo_1.get_client_id.return_value = self.client_id_1
        self.mock_repo_2.get_client_id.return_value = self.client_id_2

        self.repo = UnionAlbumsRepository([self.mock_repo_1, self.mock_repo_2])

    def test_get_available_free_space(self):
        # Arrange
        self.mock_repo_1.get_available_free_space.return_value = 100
        self.mock_repo_2.get_available_free_space.return_value = 200

        # Act
        total_space = self.repo.get_available_free_space()

        # Assert
        self.assertEqual(total_space, 300)

    def test_get_album_by_id(self):
        # Arrange
        album_id = AlbumId(self.client_id_1, ObjectId())
        expected_album = Album(id=album_id, name="Test", parent_album_id=None)
        self.mock_repo_1.get_album_by_id.return_value = expected_album

        # Act
        result = self.repo.get_album_by_id(album_id)

        # Assert
        self.assertEqual(result, expected_album)
        self.mock_repo_1.get_album_by_id.assert_called_once_with(album_id)
        self.mock_repo_2.get_album_by_id.assert_not_called()

    def test_get_all_albums(self):
        # Arrange
        album_1 = Album(
            id=AlbumId(self.client_id_1, ObjectId()), name="1", parent_album_id=None
        )
        album_2 = Album(
            id=AlbumId(self.client_id_2, ObjectId()), name="2", parent_album_id=None
        )
        self.mock_repo_1.get_all_albums.return_value = [album_1]
        self.mock_repo_2.get_all_albums.return_value = [album_2]

        # Act
        result = self.repo.get_all_albums()

        # Assert
        self.assertEqual(len(result), 2)
        self.assertIn(album_1, result)
        self.assertIn(album_2, result)

    def test_create_album__selects_repo_with_most_free_space(self):
        # Arrange
        self.mock_repo_1.get_available_free_space.return_value = 100
        self.mock_repo_2.get_available_free_space.return_value = 200
        expected_album = Album(
            id=AlbumId(self.client_id_2, ObjectId()), name="New", parent_album_id=None
        )
        self.mock_repo_2.create_album.return_value = expected_album

        # Act
        result = self.repo.create_album("New", None)

        # Assert
        self.assertEqual(result, expected_album)
        self.mock_repo_1.create_album.assert_not_called()
        self.mock_repo_2.create_album.assert_called_once_with("New", None)

    def test_delete_many_albums__groups_by_client_id(self):
        # Arrange
        album_id_1 = AlbumId(self.client_id_1, ObjectId())
        album_id_2 = AlbumId(self.client_id_2, ObjectId())
        album_id_3 = AlbumId(self.client_id_1, ObjectId())

        # Act
        self.repo.delete_many_albums([album_id_1, album_id_2, album_id_3])

        # Assert
        self.mock_repo_1.delete_many_albums.assert_called_once()
        call_args_1 = self.mock_repo_1.delete_many_albums.call_args[0][0]
        self.assertCountEqual(call_args_1, [album_id_1, album_id_3])

        self.mock_repo_2.delete_many_albums.assert_called_once()
        call_args_2 = self.mock_repo_2.delete_many_albums.call_args[0][0]
        self.assertCountEqual(call_args_2, [album_id_2])

    def test_update_many_albums__groups_by_client_id(self):
        # Arrange
        req_1 = UpdateAlbumRequest(AlbumId(self.client_id_1, ObjectId()), new_name="1")
        req_2 = UpdateAlbumRequest(AlbumId(self.client_id_2, ObjectId()), new_name="2")
        req_3 = UpdateAlbumRequest(AlbumId(self.client_id_1, ObjectId()), new_name="3")

        # Act
        self.repo.update_many_albums([req_1, req_2, req_3])

        # Assert
        self.mock_repo_1.update_many_albums.assert_called_once()
        call_args_1 = self.mock_repo_1.update_many_albums.call_args[0][0]
        self.assertCountEqual(call_args_1, [req_1, req_3])

        self.mock_repo_2.update_many_albums.assert_called_once()
        call_args_2 = self.mock_repo_2.update_many_albums.call_args[0][0]
        self.assertCountEqual(call_args_2, [req_2])

    def test_get_client_id__raises_not_implemented_error(self):
        with self.assertRaisesRegex(
            NotImplementedError, "Union repository does not have a single client ID"
        ):
            self.repo.get_client_id()

    def test_get_album_by_id__unknown_client_id__raises_value_error(self):
        album_id = AlbumId(ObjectId(), ObjectId())
        with self.assertRaisesRegex(
            ValueError, f"No repository found for client {album_id.client_id}"
        ):
            self.repo.get_album_by_id(album_id)

    def test_delete_album__unknown_client_id__raises_value_error(self):
        album_id = AlbumId(ObjectId(), ObjectId())
        with self.assertRaisesRegex(
            ValueError, f"No repository found for client {album_id.client_id}"
        ):
            self.repo.delete_album(album_id)

    def test_delete_album__calls_correct_repo(self):
        album_id = AlbumId(self.client_id_1, ObjectId())
        self.repo.delete_album(album_id)
        self.mock_repo_1.delete_album.assert_called_once_with(album_id)
        self.mock_repo_2.delete_album.assert_not_called()

    def test_delete_many_albums__unknown_client_id__raises_value_error(self):
        unknown_client_id = ObjectId()
        album_ids = [AlbumId(unknown_client_id, ObjectId())]
        with self.assertRaisesRegex(
            ValueError, f"No repository found for client {unknown_client_id}"
        ):
            self.repo.delete_many_albums(album_ids)

    def test_update_album__unknown_client_id__raises_value_error(self):
        album_id = AlbumId(ObjectId(), ObjectId())
        updates = UpdatedAlbumFields(new_name="New Name")
        with self.assertRaisesRegex(
            ValueError, f"No repository found for client {album_id.client_id}"
        ):
            self.repo.update_album(album_id, updates)

    def test_update_album__calls_correct_repo(self):
        album_id = AlbumId(self.client_id_1, ObjectId())
        updates = UpdatedAlbumFields(new_name="New Name")
        self.repo.update_album(album_id, updates)
        self.mock_repo_1.update_album.assert_called_once_with(album_id, updates)
        self.mock_repo_2.update_album.assert_not_called()

    def test_update_many_albums__unknown_client_id__raises_value_error(self):
        unknown_client_id = ObjectId()
        request = UpdateAlbumRequest(
            AlbumId(unknown_client_id, ObjectId()), new_name="Name"
        )
        with self.assertRaisesRegex(
            ValueError, f"No repository found for client {unknown_client_id}"
        ):
            self.repo.update_many_albums([request])

    def test_find_child_albums__aggregates_results(self):
        parent_id = AlbumId(self.client_id_1, ObjectId())
        child_1 = Album(
            id=AlbumId(self.client_id_1, ObjectId()),
            name="1",
            parent_album_id=parent_id,
        )
        child_2 = Album(
            id=AlbumId(self.client_id_2, ObjectId()),
            name="2",
            parent_album_id=parent_id,
        )

        self.mock_repo_1.find_child_albums.return_value = [child_1]
        self.mock_repo_2.find_child_albums.return_value = [child_2]

        children = self.repo.find_child_albums(parent_id)

        self.assertEqual(len(children), 2)
        self.assertIn(child_1, children)
        self.assertIn(child_2, children)
        self.mock_repo_1.find_child_albums.assert_called_once_with(parent_id)
        self.mock_repo_2.find_child_albums.assert_called_once_with(parent_id)

    def test_count_child_albums__sums_results(self):
        parent_id = AlbumId(self.client_id_1, ObjectId())
        self.mock_repo_1.count_child_albums.return_value = 5
        self.mock_repo_2.count_child_albums.return_value = 3

        count = self.repo.count_child_albums(parent_id)

        self.assertEqual(count, 8)
        self.mock_repo_1.count_child_albums.assert_called_once_with(parent_id)
        self.mock_repo_2.count_child_albums.assert_called_once_with(parent_id)
