from datetime import datetime
import unittest

from bson import ObjectId

from photos_drive.clean.clean_system import (
    TRASH_ALBUM_TITLE,
    GPhotosMediaItemKey,
    SystemCleaner,
)
from photos_drive.shared.core.albums.album_id import AlbumId
from photos_drive.shared.core.albums.repository.mongodb import (
    MongoDBAlbumsRepository,
)
from photos_drive.shared.core.config.inmemory_config import InMemoryConfig
from photos_drive.shared.core.databases.mongodb import (
    MongoDBClientsRepository,
)
from photos_drive.shared.core.media_items.repository.base import (
    CreateMediaItemRequest,
)
from photos_drive.shared.core.media_items.repository.mongodb import (
    MongoDBMediaItemsRepository,
)
from photos_drive.shared.core.storage.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from photos_drive.shared.core.storage.gphotos.testing import (
    FakeItemsRepository,
)
from photos_drive.shared.core.storage.gphotos.testing.fake_client import (
    FakeGPhotosClient,
)
from photos_drive.shared.core.testing.mock_mongo_client import (
    create_mock_mongo_client,
)

MOCK_FILE_HASH = b'\x8a\x19\xdd\xdeg\xdd\x96\xf2'

MOCK_ALBUM_ID = AlbumId(
    ObjectId("5f50c31e8a7d4b1c9c9b0b22"),
    ObjectId("5f50c31e8a7d4b1c9c9b0b23"),
)

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0)


class SystemCleanerTests(unittest.TestCase):
    def test_clean_deletes_unattached_albums(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDBClientsRepository()
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)

        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(
            client_id, create_mock_mongo_client(1000)
        )
        albums_repo = MongoDBAlbumsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )
        media_items_repo = MongoDBMediaItemsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )

        # Test setup 2: Set up the root album
        root_album = albums_repo.create_album('', None)
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)

        # Test setup 3: Attach 'Archives' in root album but others not
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', None)
        album_2010 = albums_repo.create_album('2010', None)
        album_2011 = albums_repo.create_album('2011', None)

        # Test setup 4: Add an image to Archives
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/dog.png', 'dog.png'
        )
        media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [dog_upload_token]
            )
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=archives_album.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
                mime_type='image/png',
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
        items_to_delete = cleaner.find_item_to_delete()
        clean_results = cleaner.delete_items(items_to_delete)

        # Assert: check on the items to be deleted
        self.assertSetEqual(
            items_to_delete.album_ids_to_delete,
            set([photos_album.id, album_2010.id, album_2011.id]),
        )
        self.assertSetEqual(items_to_delete.media_item_ids_to_delete, set())
        self.assertSetEqual(items_to_delete.gphotos_media_item_ids_to_delete, set())

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 3)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 0)
        self.assertEqual(clean_results.num_media_items_deleted, 0)

        # Assert: check that there are only 2 albums: root and Archives
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[1].id, archives_album.id)

        # Assert: check that there is only one photo: dog.png
        gmedia_items = gphotos_client.media_items().search_for_media_items()
        self.assertEqual(len(gmedia_items), 1)
        self.assertEqual(gmedia_items[0].filename, 'dog.png')

    def test_clean_with_trash_album_deletes_unattached_media_items(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDBClientsRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        albums_repo = MongoDBAlbumsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )
        media_items_repo = MongoDBMediaItemsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )

        # Test setup 2: Set up the root album
        root_album = albums_repo.create_album('', None)
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)

        # Test setup 3: Attach 'Archives' in root album but others not
        archives_album = albums_repo.create_album('Archives', root_album.id)

        # Test setup 4: Add two images, with dog.png attached to Archives
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/dog.png', 'dog.png'
        )
        dog_media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [dog_upload_token]
            )
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=dog_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=archives_album.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
                mime_type='image/png',
            )
        )
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
                album_id=MOCK_ALBUM_ID,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
                mime_type='image/png',
            )
        )

        # Test setup 5: create trash album
        trash_album = gphotos_client.albums().create_album(TRASH_ALBUM_TITLE)

        # Act: clean the system
        cleaner = SystemCleaner(
            config,
            albums_repo,
            media_items_repo,
            gphotos_clients_repo,
            mongodb_clients_repo,
        )
        items_to_delete = cleaner.find_item_to_delete()
        clean_results = cleaner.delete_items(cleaner.find_item_to_delete())

        # Assert: check on items to be deleted
        self.assertSetEqual(items_to_delete.album_ids_to_delete, set())
        self.assertSetEqual(
            items_to_delete.media_item_ids_to_delete, set([cat_media_item.id])
        )
        self.assertSetEqual(
            items_to_delete.gphotos_media_item_ids_to_delete,
            set(
                [
                    GPhotosMediaItemKey(
                        client_id=ObjectId(gphotos_client_id),
                        object_id=cat_media_items_results.newMediaItemResults[
                            0
                        ].mediaItem.id,
                    )
                ]
            ),
        )

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 0)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 1)
        self.assertEqual(clean_results.num_media_items_deleted, 1)

        # Assert: check that there are only 2 albums: root and Archives
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[1].id, archives_album.id)

        # Assert: check that there is one photo in trash
        gmedia_items = gphotos_client.media_items().search_for_media_items(
            album_id=trash_album.id
        )
        self.assertEqual(len(gmedia_items), 1)
        self.assertEqual(gmedia_items[0].filename, 'cat.png')

    def test_clean_moves_unattached_gmedia_items_to_trash_album(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDBClientsRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        albums_repo = MongoDBAlbumsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )
        media_items_repo = MongoDBMediaItemsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )

        # Test setup 2: Set up the root album
        root_album = albums_repo.create_album('', None)
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)

        # Test setup 3: Attach 'Archives' in root album but others not
        archives_album = albums_repo.create_album('Archives', root_album.id)

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
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=dog_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=archives_album.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
                mime_type='image/png',
            )
        )
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
                album_id=MOCK_ALBUM_ID,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
                mime_type='image/png',
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
        items_to_delete = cleaner.find_item_to_delete()
        clean_results = cleaner.delete_items(items_to_delete)

        # Assert: check on items to be deleted
        self.assertSetEqual(items_to_delete.album_ids_to_delete, set())
        self.assertSetEqual(
            items_to_delete.media_item_ids_to_delete, set([cat_media_item.id])
        )
        self.assertSetEqual(
            items_to_delete.gphotos_media_item_ids_to_delete,
            set(
                [
                    GPhotosMediaItemKey(
                        client_id=ObjectId(gphotos_client_id),
                        object_id=cat_media_items_results.newMediaItemResults[
                            0
                        ].mediaItem.id,
                    )
                ]
            ),
        )

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 0)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 1)
        self.assertEqual(clean_results.num_media_items_deleted, 1)

        # Assert: check that there are only 2 albums: root and Archives
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[1].id, archives_album.id)

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
        mongodb_clients_repo = MongoDBClientsRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        albums_repo = MongoDBAlbumsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )
        media_items_repo = MongoDBMediaItemsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )

        # Test setup 2: Set up the root album
        root_album = albums_repo.create_album('', None)
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)

        # Test setup 3: Set up albums
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        albums_repo.create_album('2010', photos_album.id)

        # Act: clean the system
        cleaner = SystemCleaner(
            config,
            albums_repo,
            media_items_repo,
            gphotos_clients_repo,
            mongodb_clients_repo,
        )
        items_to_delete = cleaner.find_item_to_delete()
        clean_results = cleaner.delete_items(cleaner.find_item_to_delete())

        # Assert: check on items to delete
        self.assertSetEqual(items_to_delete.album_ids_to_delete, set())
        self.assertSetEqual(items_to_delete.media_item_ids_to_delete, set())
        self.assertSetEqual(items_to_delete.gphotos_media_item_ids_to_delete, set())

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 3)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 0)
        self.assertEqual(clean_results.num_media_items_deleted, 0)

        # Assert: check that there is only 1 albums: root
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].id, root_album.id)

    def test_clean_deletes_media_items_with_false_album_id(
        self,
    ):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDBClientsRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        albums_repo = MongoDBAlbumsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )
        media_items_repo = MongoDBMediaItemsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )

        # Test setup 2: Set up the root album
        root_album = albums_repo.create_album('', None)
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)
        albums_repo.create_album('Archives', root_album.id)

        # Test setup 3: Add a new photo to gphotos
        cat_upload_token = gphotos_client.media_items().upload_photo(
            'cat.png', 'cat.png'
        )
        cat_media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [cat_upload_token]
            )
        )
        media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=cat_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=MOCK_ALBUM_ID,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
                mime_type='image/png',
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
        items_to_delete = cleaner.find_item_to_delete()
        clean_results = cleaner.delete_items(cleaner.find_item_to_delete())

        # Assert: check on items to delete
        self.assertSetEqual(items_to_delete.album_ids_to_delete, set())
        self.assertSetEqual(
            items_to_delete.media_item_ids_to_delete,
            set([media_item.id]),
        )
        self.assertSetEqual(
            items_to_delete.gphotos_media_item_ids_to_delete,
            set(
                [
                    GPhotosMediaItemKey(
                        client_id=ObjectId(gphotos_client_id),
                        object_id=cat_media_items_results.newMediaItemResults[
                            0
                        ].mediaItem.id,
                    )
                ]
            ),
        )

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 1)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 1)
        self.assertEqual(clean_results.num_media_items_deleted, 1)

        # Assert: check the albums
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].id, root_album.id)

    def test_clean_fixes_albums_with_false_gmedia_item_ids(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDBClientsRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        albums_repo = MongoDBAlbumsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )
        media_items_repo = MongoDBMediaItemsRepository(
            client_id,
            mongodb_clients_repo.get_client_by_id(client_id),
            mongodb_clients_repo,
        )

        # Test setup 2: Set up the root album and archives album
        root_album = albums_repo.create_album('', None)
        config = InMemoryConfig()
        config.set_root_album_id(root_album.id)
        archives_album = albums_repo.create_album('Archives', root_album.id)

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
                album_id=archives_album.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
                mime_type='image/png',
            )
        )

        # Test setup 4: Add a new photo to DB but not to gphotos
        false_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id='123',
                album_id=archives_album.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
                mime_type='image/png',
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
        items_to_delete = cleaner.find_item_to_delete()
        clean_results = cleaner.delete_items(cleaner.find_item_to_delete())

        # Assert: check on items to delete
        self.assertSetEqual(items_to_delete.album_ids_to_delete, set())
        self.assertSetEqual(
            items_to_delete.media_item_ids_to_delete,
            set([false_media_item.id]),
        )
        self.assertSetEqual(items_to_delete.gphotos_media_item_ids_to_delete, set())

        # Assert: check on clean results
        self.assertEqual(clean_results.num_albums_deleted, 0)
        self.assertEqual(clean_results.num_gmedia_items_moved_to_trash, 0)
        self.assertEqual(clean_results.num_media_items_deleted, 1)

        # Assert: check the albums
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[1].id, archives_album.id)

        # Assert: check on the meda items
        media_items = media_items_repo.get_all_media_items()
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0], cat_media_item)
