from pyfakefs.fake_filesystem_unittest import TestCase
from bson.objectid import ObjectId

from sharded_photos_drive_cli_client.diff.get_diffs import (
    DiffResults,
    FolderSyncDiff,
    LocalFile,
    RemoteFile,
)
from sharded_photos_drive_cli_client.shared.config.inmemory_config import InMemoryConfig
from sharded_photos_drive_cli_client.shared.gphotos.testing.fake_items_repository import (
    FakeItemsRepository,
)
from sharded_photos_drive_cli_client.shared.gphotos.testing.fake_client import (
    FakeGPhotosClient,
)
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
from sharded_photos_drive_cli_client.shared.mongodb.testing.mock_mongo_client import (
    create_mock_mongo_client,
)


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
        mongodb_client = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        config = InMemoryConfig()
        config.add_mongo_db_client(mongodb_client)
        gphotos_client_id = config.add_gphotos_client(gphotos_client)
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album(
            album_name='', parent_album_id=None, child_album_ids=[], media_item_ids=[]
        )
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        photos_album = albums_repo.create_album('Photos', archives_album.id, [], [])
        album_2010 = albums_repo.create_album('2010', photos_album.id, [], [])
        album_2011 = albums_repo.create_album('2011', photos_album.id, [], [])
        config.set_root_album_id(root_album.id)
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
            UpdatedAlbumFields(new_child_album_ids=[album_2010.id, album_2011.id]),
        )
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.jpg', 'dog.jpg'
        )
        media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.jpg',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([dog_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[media_item.id]),
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
                        key='Archives/Photos/2011/cat.jpg',
                        local_relative_file_path='./Archives/Photos/2011/cat.jpg',
                    ),
                ],
            ),
        )

    def test_get_diffs__missing_files_on_local__returns_diff(self):
        # Test setup: create directories
        self.fs.create_dir('/Archives/Photos/2010')
        self.fs.create_dir('/Archives/Photos/2011')
        self.fs.create_file('/Archives/Photos/2010/dog.jpg', contents='Dog')

        # Test setup: set up the cloud
        mongodb_client = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        config = InMemoryConfig()
        config.add_mongo_db_client(mongodb_client)
        gphotos_client_id = config.add_gphotos_client(gphotos_client)
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album(
            album_name='', parent_album_id=None, child_album_ids=[], media_item_ids=[]
        )
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        photos_album = albums_repo.create_album('Photos', archives_album.id, [], [])
        album_2010 = albums_repo.create_album('2010', photos_album.id, [], [])
        album_2011 = albums_repo.create_album('2011', photos_album.id, [], [])
        config.set_root_album_id(root_album.id)
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
            UpdatedAlbumFields(new_child_album_ids=[album_2010.id, album_2011.id]),
        )
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.jpg', 'dog.jpg'
        )
        cat_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2011/cat.jpg', 'cat.jpg'
        )
        dog_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.jpg',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([dog_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
            )
        )
        cat_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.jpg',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([cat_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[dog_media_item.id]),
        )
        albums_repo.update_album(
            album_2011.id,
            UpdatedAlbumFields(new_media_item_ids=[cat_media_item.id]),
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
                        key='Archives/Photos/2011/cat.jpg',
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
        mongodb_client = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        config = InMemoryConfig()
        config.add_mongo_db_client(mongodb_client)
        gphotos_client_id = config.add_gphotos_client(gphotos_client)
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album(
            album_name='', parent_album_id=None, child_album_ids=[], media_item_ids=[]
        )
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        photos_album = albums_repo.create_album('Photos', archives_album.id, [], [])
        album_2010 = albums_repo.create_album('2010', photos_album.id, [], [])
        config.set_root_album_id(root_album.id)
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
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.jpg', 'dog.jpg'
        )
        media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.jpg',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([dog_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[media_item.id]),
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
        mongodb_client = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        config = InMemoryConfig()
        config.add_mongo_db_client(mongodb_client)
        gphotos_client_id = config.add_gphotos_client(gphotos_client)
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album(
            album_name='', parent_album_id=None, child_album_ids=[], media_item_ids=[]
        )
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        photos_album = albums_repo.create_album('Photos', archives_album.id, [], [])
        album_2010 = albums_repo.create_album('2010', photos_album.id, [], [])
        config.set_root_album_id(root_album.id)
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
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.jpg', 'dog.jpg'
        )
        media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.jpg',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([dog_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[media_item.id]),
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
        mongodb_client = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        config = InMemoryConfig()
        config.add_mongo_db_client(mongodb_client)
        gphotos_client_id = config.add_gphotos_client(gphotos_client)
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup: create content on the cloud
        root_album = albums_repo.create_album(
            album_name='', parent_album_id=None, child_album_ids=[], media_item_ids=[]
        )
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        photos1_album = albums_repo.create_album('Photos', archives_album.id, [], [])
        album_2010 = albums_repo.create_album('2010', photos1_album.id, [], [])
        laptop_album = albums_repo.create_album('Laptop', root_album.id, [], [])
        photos2_album = albums_repo.create_album('Photos', laptop_album.id, [], [])
        album_2020 = albums_repo.create_album('2020', photos2_album.id, [], [])
        config.set_root_album_id(root_album.id)
        albums_repo.update_album(
            root_album.id,
            UpdatedAlbumFields(
                new_child_album_ids=[archives_album.id, laptop_album.id]
            ),
        )
        albums_repo.update_album(
            archives_album.id,
            UpdatedAlbumFields(new_child_album_ids=[photos1_album.id]),
        )
        albums_repo.update_album(
            photos1_album.id,
            UpdatedAlbumFields(new_child_album_ids=[album_2010.id]),
        )
        albums_repo.update_album(
            laptop_album.id,
            UpdatedAlbumFields(new_child_album_ids=[photos2_album.id]),
        )
        albums_repo.update_album(
            photos2_album.id,
            UpdatedAlbumFields(new_child_album_ids=[album_2020.id]),
        )
        cat_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/cat.jpg', 'cat.jpg'
        )
        cat_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.jpg',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([cat_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[cat_media_item.id]),
        )
        boat_upload_token = gphotos_client.media_items().upload_photo(
            './Laptop/Photos/2020/boat.jpg', 'boat.jpg'
        )
        boat_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='boat.jpg',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=gphotos_client.media_items()
                .add_uploaded_photos_to_gphotos([boat_upload_token])
                .newMediaItemResults[0]
                .mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2020.id,
            UpdatedAlbumFields(new_media_item_ids=[boat_media_item.id]),
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
                        key='Photos/2010/cat.jpg',
                        remote_relative_file_path='Archives/Photos/2010/cat.jpg',
                    )
                ],
                missing_local_files_in_remote=[
                    LocalFile(
                        key='Photos/2010/dog.jpg',
                        local_relative_file_path='./Archives/Photos/2010/dog.jpg',
                    )
                ],
            ),
        )
