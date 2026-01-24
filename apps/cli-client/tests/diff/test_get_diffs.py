from datetime import datetime, timezone

from bson.objectid import ObjectId
from pyfakefs.fake_filesystem_unittest import TestCase

from photos_drive.diff.get_diffs import (
    DiffResults,
    FolderSyncDiff,
    LocalFile,
    RemoteFile,
)
from photos_drive.shared.core.albums.repository.mongodb import (
    MongoDBAlbumsRepository,
)
from photos_drive.shared.core.clients.mongodb import (
    MongoDbTransactionRepository,
)
from photos_drive.shared.core.config.inmemory_config import InMemoryConfig
from photos_drive.shared.core.media_items.repository.base import (
    CreateMediaItemRequest,
)
from photos_drive.shared.core.media_items.repository.mongodb import (
    MongoDBMediaItemsRepository,
)
from photos_drive.shared.core.storage.gphotos.testing import (
    FakeGPhotosClient,
    FakeItemsRepository,
)
from photos_drive.shared.core.testing import (
    create_mock_mongo_client,
)
from photos_drive.shared.utils.hashes.xxhash import compute_file_hash

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0, tzinfo=timezone.utc)


class FolderSyncDiffTests(TestCase):
    def setUp(self):
        # Set up the fake file system
        self.setUpPyfakefs()

    def test_get_diffs__missing_files_on_cloud__returns_diff(self):
        # Test setup: create directories
        self.fs.create_dir('/Archives/Photos/2010')
        self.fs.create_dir('/Archives/Photos/2011')
        self.fs.create_file('/Archives/Photos/2010/dog.jpg', contents='Dog')
        self.fs.create_file('/Archives/Photos/2011/cat.jpg', contents='Cat')

        # Test setup: set up the cloud
        config = InMemoryConfig()
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        mongodb_clients_repo = MongoDbTransactionRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
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

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album('', None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos_album.id)
        albums_repo.create_album('2011', photos_album.id)
        config.set_root_album_id(root_album.id)
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.jpg', 'dog.jpg'
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.jpg',
                file_hash=compute_file_hash('./Archives/Photos/2010/dog.jpg'),
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([dog_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: compute the diff
        diffs_comparator = FolderSyncDiff(config, albums_repo, media_items_repo)
        diff_results = diffs_comparator.get_diffs('.', '')

        # Assert: verify the diff
        self.assertEqual(
            diff_results,
            DiffResults(
                missing_remote_files_in_local=[],
                missing_local_files_in_remote=[
                    LocalFile(
                        key='Archives/Photos/2011/cat.jpg:cfe93190249dd0d3',
                        local_relative_file_path='./Archives/Photos/2011/cat.jpg',
                    )
                ],
            ),
        )

    def test_get_diffs__missing_files_on_local__returns_diff(self):
        # Test setup: create directories
        self.fs.create_dir('/Archives/Photos/2010')
        self.fs.create_dir('/Archives/Photos/2011')
        self.fs.create_file('/Archives/Photos/2010/dog.jpg', contents='Dog')

        # Test setup: set up the cloud
        config = InMemoryConfig()
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        mongodb_clients_repo = MongoDbTransactionRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
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

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album(album_name='', parent_album_id=None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos_album.id)
        album_2011 = albums_repo.create_album('2011', photos_album.id)
        config.set_root_album_id(root_album.id)
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.jpg', 'dog.jpg'
        )
        cat_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2011/cat.jpg', 'cat.jpg'
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.jpg',
                file_hash=compute_file_hash('./Archives/Photos/2010/dog.jpg'),
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([dog_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.jpg',
                file_hash=b'\x8a\x19\xdd\xdeg\xdd\x96\xf2',
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([cat_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
                album_id=album_2011.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: compute the diff
        diffs_comparator = FolderSyncDiff(config, albums_repo, media_items_repo)
        diff_results = diffs_comparator.get_diffs('.', '')

        # Assert: verify the diff
        self.assertEqual(
            diff_results,
            DiffResults(
                missing_remote_files_in_local=[
                    RemoteFile(
                        key='Archives/Photos/2011/cat.jpg:8a19ddde67dd96f2',
                        remote_relative_file_path='/Archives/Photos/2011/cat.jpg',
                    )
                ],
                missing_local_files_in_remote=[],
            ),
        )

    def test_get_diffs__non_image_files_on_local__returns_diff(self):
        # Test setup: create directories
        self.fs.create_dir('/Archives/Photos/2010')
        self.fs.create_dir('/Archives/Photos/2011')
        self.fs.create_file('/Archives/Photos/2010/dog.jpg', contents='Dog')
        self.fs.create_file('/Archives/Photos/2010/.DS_Store', contents='-')
        self.fs.create_file('/Archives/Photos/2011/notes.txt', contents='My notes')

        # Test setup: set up the cloud
        config = InMemoryConfig()
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        mongodb_clients_repo = MongoDbTransactionRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
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

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album('', None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos_album.id)
        config.set_root_album_id(root_album.id)
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.jpg', 'dog.jpg'
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.jpg',
                file_hash=compute_file_hash('./Archives/Photos/2010/dog.jpg'),
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([dog_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: compute the diff
        diffs_comparator = FolderSyncDiff(config, albums_repo, media_items_repo)
        diff_results = diffs_comparator.get_diffs('.', '')

        # Assert: verify the diff
        self.assertEqual(
            diff_results,
            DiffResults(
                missing_remote_files_in_local=[],
                missing_local_files_in_remote=[],
            ),
        )

    def test_get_diffs__invalid_remote_dir_path__throws_error(self):
        # Test setup: create directories
        self.fs.create_dir('/Laptop/Photos/2020')
        self.fs.create_file('/Laptop/Photos/2020/car.jpg', contents='Car')

        # Test setup: set up the cloud
        config = InMemoryConfig()
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        mongodb_clients_repo = MongoDbTransactionRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
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

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album('', None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos_album.id)
        config.set_root_album_id(root_album.id)
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.jpg', 'dog.jpg'
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.jpg',
                file_hash=b'\x8a\x19\xdd\xdeg\xdd\x96\xf2',
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([dog_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: compute the diff
        diffs_comparator = FolderSyncDiff(config, albums_repo, media_items_repo)

        # Assert: exception is thrown
        with self.assertRaisesRegex(
            ValueError, 'Remote dir path Laptop does not exist in the system'
        ):
            diffs_comparator.get_diffs('./Laptop', 'Laptop')

    def test_get_diffs__valid_remote_local_dir_paths__returns_diffs_only_in_paths(self):
        # Test setup: create directories
        self.fs.create_dir('/Archives/Photos/2010')
        self.fs.create_file('/Archives/Photos/2010/dog.jpg', contents='Dog')
        self.fs.create_dir('/Laptop/Photos/2020')
        self.fs.create_file('/Laptop/Photos/2020/car.jpg', contents='Car')

        # Test setup: set up the cloud
        config = InMemoryConfig()
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        mongodb_clients_repo = MongoDbTransactionRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
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

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album('', None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos1_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos1_album.id)
        laptop_album = albums_repo.create_album('Laptop', root_album.id)
        photos2_album = albums_repo.create_album('Photos', laptop_album.id)
        album_2020 = albums_repo.create_album('2020', photos2_album.id)
        config.set_root_album_id(root_album.id)
        cat_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/cat.jpg', 'cat.jpg'
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.jpg',
                file_hash=b'\x8a\x19\xdd\xdeg\xdd\x96\xf2',
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([cat_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )
        boat_upload_token = gphotos_client.media_items().upload_photo(
            './Laptop/Photos/2020/boat.jpg', 'boat.jpg'
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='boat.jpg',
                file_hash=b'\x8a\x19\xdd\xdeg\xdd\x96\xf2',
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([boat_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
                album_id=album_2020.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: compute the diff
        diffs_comparator = FolderSyncDiff(config, albums_repo, media_items_repo)
        diff_results = diffs_comparator.get_diffs('./Archives', 'Archives')

        # Assert: verify diffs while ignoring other folders / albums not prefixed
        # with 'Archives'
        self.assertEqual(
            diff_results,
            DiffResults(
                missing_remote_files_in_local=[
                    RemoteFile(
                        key='Photos/2010/cat.jpg:8a19ddde67dd96f2',
                        remote_relative_file_path='Archives/Photos/2010/cat.jpg',
                    )
                ],
                missing_local_files_in_remote=[
                    LocalFile(
                        key='Photos/2010/dog.jpg:33aaa5ec9adeadaa',
                        local_relative_file_path='./Archives/Photos/2010/dog.jpg',
                    )
                ],
            ),
        )

    def test_get_diffs__unknown_image_in_remote_dir_path_album(self):
        # Test setup: create directories
        self.fs.create_dir('/Archives/Photos/2010')
        self.fs.create_file('/Archives/Photos/2010/dog.jpg', contents='Dog')

        # Test setup: set up the cloud
        config = InMemoryConfig()
        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        mongodb_clients_repo = MongoDbTransactionRepository()
        client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(client_id, create_mock_mongo_client())
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

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album('', None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos1_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos1_album.id)
        config.set_root_album_id(root_album.id)
        cat_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/cat.jpg', 'cat.jpg'
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.jpg',
                file_hash=b'\x8a\x19\xdd\xdeg\xdd\x96\xf2',
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([cat_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
                album_id=archives_album.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.jpg', 'dog.jpg'
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.jpg',
                file_hash=compute_file_hash('./Archives/Photos/2010/dog.jpg'),
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([dog_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: compute the diff
        diffs_comparator = FolderSyncDiff(config, albums_repo, media_items_repo)
        diff_results = diffs_comparator.get_diffs('./Archives', 'Archives')

        # Assert: verify diffs while ignoring other folders / albums not prefixed
        # with 'Archives'
        self.assertEqual(
            diff_results,
            DiffResults(
                missing_remote_files_in_local=[
                    RemoteFile(
                        key='cat.jpg:8a19ddde67dd96f2',
                        remote_relative_file_path='Archives/cat.jpg',
                    )
                ],
                missing_local_files_in_remote=[],
            ),
        )
