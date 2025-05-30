import unittest
from bson.objectid import ObjectId

from sharded_photos_drive_cli_client.shared.gphotos.testing import (
    FakeItemsRepository,
    FakeGPhotosClient,
)
from sharded_photos_drive_cli_client.shared.mongodb.albums_pruner import AlbumsPruner
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.albums_repository import (
    AlbumsRepositoryImpl,
    UpdatedAlbumFields,
)
from sharded_photos_drive_cli_client.shared.mongodb.media_items_repository import (
    MediaItemsRepositoryImpl,
    CreateMediaItemRequest,
)
from sharded_photos_drive_cli_client.shared.mongodb.testing import (
    create_mock_mongo_client,
)

MOCK_FILE_HASH = b'\x8a\x19\xdd\xdeg\xdd\x96\xf2'


class AlbumsPrunerTests(unittest.TestCase):
    def test_prune_album__descendants_all_empty_albums(self):
        # Test setup: Build the objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(ObjectId(), create_mock_mongo_client())
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup: Set up the existing albums
        root_album = albums_repo.create_album('', None, [], [])
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        photos_album = albums_repo.create_album('Photos', archives_album.id, [], [])
        album_2010 = albums_repo.create_album('2010', photos_album.id, [], [])
        albums_repo.update_album(
            root_album.id,
            UpdatedAlbumFields(new_child_album_ids=[archives_album.id]),
        )
        albums_repo.update_album(
            archives_album.id,
            UpdatedAlbumFields(new_child_album_ids=[photos_album.id]),
        )
        albums_repo.update_album(
            photos_album.id,
            UpdatedAlbumFields(new_child_album_ids=[album_2010.id]),
        )

        # Act: Prune on album 2010
        pruner = AlbumsPruner(root_album.id, albums_repo, media_items_repo)
        num_albums_deleted = pruner.prune_album(album_2010.id)

        # Test assert
        self.assertEqual(num_albums_deleted, 3)

        # Test assert: Check that only the root album exists
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 1)

        # Test assert: Check that root albums is updated correctly
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(len(albums[0].child_album_ids), 0)
        self.assertEqual(len(albums[0].media_item_ids), 0)
        self.assertEqual(albums[0].parent_album_id, None)

    def test_prune_album__media_item_in_descendants(self):
        # Test setup 1: Build the GPhotos client
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')

        # Test setup 2: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(ObjectId(), create_mock_mongo_client())
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 3: Set up the existing albums
        root_album = albums_repo.create_album('', None, [], [])
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        photos_album = albums_repo.create_album('Photos', archives_album.id, [], [])
        album_2010 = albums_repo.create_album('2010', photos_album.id, [], [])
        albums_repo.update_album(
            root_album.id,
            UpdatedAlbumFields(new_child_album_ids=[archives_album.id]),
        )
        albums_repo.update_album(
            archives_album.id,
            UpdatedAlbumFields(new_child_album_ids=[photos_album.id]),
        )
        albums_repo.update_album(
            photos_album.id,
            UpdatedAlbumFields(new_child_album_ids=[album_2010.id]),
        )

        # Test setup 4: Add cat.png to Archives/
        cat_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/cat.png', 'cat.png'
        )
        cat_media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [cat_upload_token]
            )
        )
        cat_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=cat_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=archives_album.id,
            )
        )
        albums_repo.update_album(
            archives_album.id,
            UpdatedAlbumFields(new_media_item_ids=[cat_media_item.id]),
        )

        # Act: prune on 2010
        pruner = AlbumsPruner(root_album.id, albums_repo, media_items_repo)
        num_albums_deleted = pruner.prune_album(album_2010.id)

        # Test assert:
        self.assertEqual(num_albums_deleted, 2)

        # Test assert: check that cat.png is kept
        media_items = media_items_repo.get_all_media_items()
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].file_name, 'cat.png')

        # Test assert: Check that only the root/Archives album exists
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)

        # Test assert: Check that root album is updated correctly
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].child_album_ids, [albums[1].id])
        self.assertEqual(albums[0].media_item_ids, [])
        self.assertEqual(albums[0].parent_album_id, None)

        # Test assert: Check that Archives album is updated correctly
        self.assertEqual(albums[1].id, archives_album.id)
        self.assertEqual(albums[1].child_album_ids, [])
        self.assertEqual(albums[1].media_item_ids, [cat_media_item.id])
        self.assertEqual(albums[1].parent_album_id, root_album.id)

    def test_backup_pruning_3(self):
        # Test setup 1: Build the GPhotos client
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')

        # Test setup 2: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(
            ObjectId(), create_mock_mongo_client(1000)
        )
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 3: Set up the existing albums
        root_album = albums_repo.create_album('', None, [], [])
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        videos_album = albums_repo.create_album('Videos', archives_album.id, [], [])
        photos_album = albums_repo.create_album('Photos', archives_album.id, [], [])
        album_2010 = albums_repo.create_album('2010', photos_album.id, [], [])
        albums_repo.update_album(
            root_album.id,
            UpdatedAlbumFields(new_child_album_ids=[archives_album.id]),
        )
        albums_repo.update_album(
            archives_album.id,
            UpdatedAlbumFields(new_child_album_ids=[videos_album.id, photos_album.id]),
        )
        albums_repo.update_album(
            photos_album.id,
            UpdatedAlbumFields(new_child_album_ids=[album_2010.id]),
        )

        # Test setup 4: Add cat.png to Archives/Videos/cat.png
        cat_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Videos/cat.png', 'cat.png'
        )
        cat_media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [cat_upload_token]
            )
        )
        cat_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=cat_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=videos_album.id,
            )
        )
        albums_repo.update_album(
            videos_album.id,
            UpdatedAlbumFields(new_media_item_ids=[cat_media_item.id]),
        )

        # Act: Prune on 2010 album
        pruner = AlbumsPruner(root_album.id, albums_repo, media_items_repo)
        num_albums_deleted = pruner.prune_album(album_2010.id)

        # Test assert:
        self.assertEqual(num_albums_deleted, 2)

        # Test assert: check that there's only one media item
        media_items = media_items_repo.get_all_media_items()
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].file_name, 'cat.png')

        # Test assert: Check that only the root/Archives/Videos album path exists
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 3)

        # Test assert: Check that root album is updated correctly
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].child_album_ids, [archives_album.id])
        self.assertEqual(albums[0].media_item_ids, [])
        self.assertEqual(albums[0].parent_album_id, None)

        # Test assert: Check that archives album is updated correctly
        self.assertEqual(albums[1].id, archives_album.id)
        self.assertEqual(albums[1].child_album_ids, [videos_album.id])
        self.assertEqual(albums[1].media_item_ids, [])
        self.assertEqual(albums[1].parent_album_id, root_album.id)

        self.assertEqual(albums[2].id, videos_album.id)
        self.assertEqual(albums[2].child_album_ids, [])
        self.assertEqual(albums[2].media_item_ids, [cat_media_item.id])
        self.assertEqual(albums[2].parent_album_id, archives_album.id)
