import unittest

from bson import ObjectId

from sharded_photos_drive_cli_client.clean.clean_system import (
    TRASH_ALBUM_TITLE,
    SystemCleaner,
)
from sharded_photos_drive_cli_client.shared.config.inmemory_config import InMemoryConfig
from sharded_photos_drive_cli_client.shared.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from sharded_photos_drive_cli_client.shared.gphotos.testing.fake_client import (
    FakeGPhotosClient,
)
from sharded_photos_drive_cli_client.shared.gphotos.testing import (
    FakeItemsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.albums import AlbumId
from sharded_photos_drive_cli_client.shared.mongodb.albums_repository import (
    AlbumsRepositoryImpl,
    UpdatedAlbumFields,
)
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.media_items import MediaItemId
from sharded_photos_drive_cli_client.shared.mongodb.media_items_repository import (
    CreateMediaItemRequest,
    MediaItemsRepositoryImpl,
)
from sharded_photos_drive_cli_client.shared.mongodb.testing.mock_mongo_client import (
    create_mock_mongo_client,
)

MOCK_FILE_HASH = b'\x8a\x19\xdd\xdeg\xdd\x96\xf2'


class SystemCleanerTests(unittest.TestCase):
    def test_clean_deletes_unattached_albums(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(
            ObjectId(), create_mock_mongo_client(1000)
        )
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)

        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the root album
        root_album = albums_repo.create_album('', None, [], [])
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)

        # Test setup 3: Attach 'Archives' in root album but others not
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        albums_repo.create_album('Photos', None, [], [])
        albums_repo.create_album('2010', None, [], [])
        albums_repo.create_album('2011', None, [], [])
        albums_repo.update_album(
            root_album.id, UpdatedAlbumFields(new_child_album_ids=[archives_album.id])
        )

        # Test setup 4: Add an image to Archives
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/dog.png', 'dog.png'
        )
        media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [dog_upload_token]
            )
        )
        dog_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        albums_repo.update_album(
            archives_album.id,
            UpdatedAlbumFields(new_media_item_ids=[dog_media_item.id]),
        )

        # Act: clean the system
        cleaner = SystemCleaner(
            config,
            albums_repo,
            media_items_repo,
            gphotos_clients_repo,
            mongodb_clients_repo,
        )
        clean_results = cleaner.clean()

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 3)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 0)
        self.assertEqual(clean_results.num_media_items_deleted, 0)

        # Assert: check that there are only 2 albums: root and Archives
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].child_album_ids, [archives_album.id])
        self.assertEqual(albums[0].media_item_ids, [])
        self.assertEqual(albums[1].id, archives_album.id)
        self.assertEqual(albums[1].child_album_ids, [])
        self.assertEqual(albums[1].media_item_ids, [dog_media_item.id])

        # Assert: check that there is only one photo: dog.png
        gmedia_items = gphotos_client.media_items().search_for_media_items()
        self.assertEqual(len(gmedia_items), 1)
        self.assertEqual(gmedia_items[0].filename, 'dog.png')

    def test_clean_with_random_albums_deletes_albums(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(ObjectId(), create_mock_mongo_client())
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Create albums in the gphotos client
        gphotos_client.albums().create_album('To delete')
        gphotos_client.albums().create_album('Fun')
        gphotos_client.albums().create_album('Dogs')

        # Test setup 3: Create root album
        root_album = albums_repo.create_album('', None, [], [])
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)

        # Act: clean the system
        cleaner = SystemCleaner(
            config,
            albums_repo,
            media_items_repo,
            gphotos_clients_repo,
            mongodb_clients_repo,
        )
        clean_results = cleaner.clean()

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 0)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 0)
        self.assertEqual(clean_results.num_media_items_deleted, 0)

        # Assert: check that there are no albums in GPhotos
        self.assertEqual(len(gphotos_client.albums().list_albums()), 0)

        # Assert: check that there is only 1 albums: root
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].child_album_ids, [])
        self.assertEqual(albums[0].media_item_ids, [])

    def test_clean_moves_unattached_gmedia_items_to_trash_album(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(ObjectId(), create_mock_mongo_client())
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the root album
        root_album = albums_repo.create_album('', None, [], [])
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)

        # Test setup 3: Attach 'Archives' in root album but others not
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        albums_repo.update_album(
            root_album.id, UpdatedAlbumFields(new_child_album_ids=[archives_album.id])
        )

        # Test setup 4: Add two images, with dog.png attached to Archives
        # and the other not attached to anything
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/dog.png', 'dog.png'
        )
        dog_media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [dog_upload_token]
            )
        )
        dog_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=dog_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        albums_repo.update_album(
            archives_album.id,
            UpdatedAlbumFields(new_media_item_ids=[dog_media_item.id]),
        )
        cat_upload_token = gphotos_client.media_items().upload_photo(
            'cat.png', 'cat.png'
        )
        cat_media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [cat_upload_token]
            )
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=cat_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )

        # Act: clean the system
        cleaner = SystemCleaner(
            config,
            albums_repo,
            media_items_repo,
            gphotos_clients_repo,
            mongodb_clients_repo,
        )
        clean_results = cleaner.clean()

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 0)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 1)
        self.assertEqual(clean_results.num_media_items_deleted, 1)

        # Assert: check that there are only 2 albums: root and Archives
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].child_album_ids, [archives_album.id])
        self.assertEqual(albums[0].media_item_ids, [])
        self.assertEqual(albums[1].id, archives_album.id)
        self.assertEqual(albums[1].child_album_ids, [])
        self.assertEqual(albums[1].media_item_ids, [dog_media_item.id])

        # Assert: check that there is one photo in trash
        trash_album = next(
            filter(
                lambda x: x.title == TRASH_ALBUM_TITLE,
                gphotos_client.albums().list_albums(),
            )
        )
        gmedia_items = gphotos_client.media_items().search_for_media_items(
            album_id=trash_album.id
        )
        self.assertEqual(len(gmedia_items), 1)
        self.assertEqual(gmedia_items[0].filename, 'cat.png')

    def test_clean_prunes_albums(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(ObjectId(), create_mock_mongo_client())
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the root album
        root_album = albums_repo.create_album('', None, [], [])
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)

        # Test setup 3: Set up albums
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

        # Act: clean the system
        cleaner = SystemCleaner(
            config,
            albums_repo,
            media_items_repo,
            gphotos_clients_repo,
            mongodb_clients_repo,
        )
        clean_results = cleaner.clean()

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 3)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 0)
        self.assertEqual(clean_results.num_media_items_deleted, 0)

        # Assert: check that there is only 1 albums: root
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].child_album_ids, [])
        self.assertEqual(albums[0].media_item_ids, [])

    def test_clean_fixes_albums_with_false_child_album_ids_and_false_media_item_ids(
        self,
    ):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(ObjectId(), create_mock_mongo_client())
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the root album
        root_album = albums_repo.create_album('', None, [], [])
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)

        # Test setup 3: Add a new photo to gphotos
        cat_upload_token = gphotos_client.media_items().upload_photo(
            'cat.png', 'cat.png'
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
            )
        )

        # Test setup 4: Add a new gphoto to the album and with a fake media item id
        # Test setup 3: Create an Archives album with false child album ids
        archives_album = albums_repo.create_album(
            'Archives',
            root_album.id,
            [AlbumId(ObjectId(), ObjectId())],
            [
                MediaItemId(ObjectId(), ObjectId()),
                cat_media_item.id,
            ],
        )
        albums_repo.update_album(
            root_album.id,
            UpdatedAlbumFields(new_child_album_ids=[archives_album.id]),
        )

        # Act: clean the system
        cleaner = SystemCleaner(
            config,
            albums_repo,
            media_items_repo,
            gphotos_clients_repo,
            mongodb_clients_repo,
        )
        clean_results = cleaner.clean()

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 0)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 0)
        self.assertEqual(clean_results.num_media_items_deleted, 0)

        # Assert: check the albums
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].child_album_ids, [archives_album.id])
        self.assertEqual(albums[0].media_item_ids, [])
        self.assertEqual(albums[1].id, archives_album.id)
        self.assertEqual(albums[1].child_album_ids, [])
        self.assertEqual(albums[1].media_item_ids, [cat_media_item.id])
