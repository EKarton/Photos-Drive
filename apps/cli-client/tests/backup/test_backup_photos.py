import unittest
from bson.objectid import ObjectId

from sharded_photos_drive_cli_client.backup.diffs_assignments import DiffsAssigner
from sharded_photos_drive_cli_client.shared.config.inmemory_config import InMemoryConfig
from sharded_photos_drive_cli_client.shared.gphotos.testing import (
    FakeGPhotosClient,
    FakeItemsRepository,
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
from sharded_photos_drive_cli_client.shared.mongodb.media_items import GpsLocation
from sharded_photos_drive_cli_client.shared.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from sharded_photos_drive_cli_client.backup.gphotos_uploader import (
    GPhotosMediaItemUploader,
)
from sharded_photos_drive_cli_client.backup.backup_photos import PhotosBackup
from sharded_photos_drive_cli_client.backup.processed_diffs import ProcessedDiff
from sharded_photos_drive_cli_client.shared.mongodb.testing import (
    create_mock_mongo_client,
)


class TestPhotosBackup(unittest.TestCase):
    def test_backup_adding_items_to_new_db(self):
        # Test setup 1: Set up the config
        mongodb_client_1 = create_mock_mongo_client(1000)
        mongodb_client_2 = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client_1 = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        gphotos_client_2 = FakeGPhotosClient(gphotos_items_repo, 'sam@gmail.com')
        config = InMemoryConfig()
        mongodb_client_1_id = config.add_mongo_db_client(mongodb_client_1)
        config.add_mongo_db_client(mongodb_client_2)
        gphotos_client_1_id = config.add_gphotos_client(gphotos_client_1)
        gphotos_client_2_id = config.add_gphotos_client(gphotos_client_2)

        # Test setup 2: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphotos_client_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 3: Set up the root album
        root_album_obj = albums_repo.create_album('', None, [], [])
        config.set_root_album_id(root_album_obj.id)

        # Test setup 4: Build the objects for backup
        uploader = GPhotosMediaItemUploader(gphotos_client_repo)
        diffs_assigner = DiffsAssigner(config)
        backup = PhotosBackup(
            config, albums_repo, media_items_repo, uploader, diffs_assigner
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2010/dog.png',
                album_name="Archives/Photos/2010",
                file_name="dog.png",
                file_size=10,
                location=GpsLocation(latitude=-1, longitude=1),
            ),
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2010/cat.png',
                album_name="Archives/Photos/2010",
                file_name="cat.png",
                file_size=10,
                location=GpsLocation(latitude=-2, longitude=2),
            ),
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2009/fish.png',
                album_name="Archives/Photos/2009",
                file_name="fish.png",
                file_size=10,
                location=GpsLocation(latitude=-3, longitude=3),
            ),
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2009/bird.png',
                album_name="Archives/Photos/2009",
                file_name="bird.png",
                file_size=10,
                location=GpsLocation(latitude=-4, longitude=4),
            ),
        ]
        backup_results = backup.backup(diffs)

        # Test assert: check on backup results
        self.assertEqual(backup_results.num_media_items_added, 4)
        self.assertEqual(backup_results.num_media_items_deleted, 0)

        # Test assert: check that media items are made in GPhotos
        gitems_1 = gphotos_client_1.media_items().search_for_media_items()
        gitems_2 = gphotos_client_2.media_items().search_for_media_items()
        self.assertEqual(len(gitems_1), 2)
        self.assertEqual(len(gitems_2), 2)
        dog_gitem = next(filter(lambda x: x.filename == 'dog.png', gitems_1))
        cat_gitem = next(filter(lambda x: x.filename == 'cat.png', gitems_2))
        fish_gitem = next(filter(lambda x: x.filename == 'fish.png', gitems_1))
        bird_gitem = next(filter(lambda x: x.filename == 'bird.png', gitems_2))

        # Test assert: check the folders are made
        albums_1 = list(mongodb_client_1['sharded_google_photos']['albums'].find({}))
        albums_2 = list(mongodb_client_2['sharded_google_photos']['albums'].find({}))
        self.assertEqual(len(albums_1), 5)
        self.assertEqual(len(albums_2), 0)
        root_album = next(filter(lambda x: x['name'] == '', albums_1))
        archives_album = next(filter(lambda x: x['name'] == 'Archives', albums_1))
        photos_album = next(filter(lambda x: x['name'] == 'Photos', albums_1))
        album_2009 = next(filter(lambda x: x['name'] == '2009', albums_1))
        album_2010 = next(filter(lambda x: x['name'] == '2010', albums_1))

        # Test assert: check on the root folder and it's linked correctly
        self.assertIn(
            f'{mongodb_client_1_id}:{archives_album['_id']}',
            root_album['child_album_ids'],
        )
        self.assertEqual([], root_album['media_item_ids'])
        self.assertIsNone(root_album['parent_album_id'])

        # Test assert: check on the Archives folder and it's linked correctly
        self.assertIn(
            f'{mongodb_client_1_id}:{photos_album['_id']}',
            archives_album['child_album_ids'],
        )
        self.assertEqual([], archives_album['media_item_ids'])
        self.assertIn(
            f'{root_album_obj.id.client_id}:{root_album_obj.id.object_id}',
            archives_album['parent_album_id'],
        )

        # Test assert: check on the Photos folder and it's linked correctly
        self.assertIn(
            f'{mongodb_client_1_id}:{album_2009['_id']}',
            photos_album['child_album_ids'],
        )
        self.assertIn(
            f'{mongodb_client_1_id}:{album_2010['_id']}',
            photos_album['child_album_ids'],
        )
        self.assertEqual([], photos_album['media_item_ids'])
        self.assertIn(
            f'{mongodb_client_1_id}:{archives_album['_id']}',
            photos_album['parent_album_id'],
        )

        # Test assert: check the media items in the db are made
        mitems_1 = list(
            mongodb_client_1['sharded_google_photos']['media_items'].find({})
        )
        mitems_2 = list(
            mongodb_client_2['sharded_google_photos']['media_items'].find({})
        )
        self.assertEqual(len(mitems_1), 4)
        self.assertEqual(len(mitems_2), 0)
        dog_item = next(filter(lambda x: x['file_name'] == 'dog.png', mitems_1))
        cat_item = next(filter(lambda x: x['file_name'] == 'cat.png', mitems_1))
        fish_item = next(filter(lambda x: x['file_name'] == 'fish.png', mitems_1))
        bird_item = next(filter(lambda x: x['file_name'] == 'bird.png', mitems_1))

        # Test assert: check that the media items in the db are linked to GPhotos
        self.assertEqual(dog_item['gphotos_client_id'], gphotos_client_1_id)
        self.assertEqual(dog_item['gphotos_media_item_id'], dog_gitem.id)
        self.assertEqual(cat_item['gphotos_client_id'], gphotos_client_2_id)
        self.assertEqual(cat_item['gphotos_media_item_id'], cat_gitem.id)
        self.assertEqual(fish_item['gphotos_client_id'], gphotos_client_1_id)
        self.assertEqual(fish_item['gphotos_media_item_id'], fish_gitem.id)
        self.assertEqual(bird_item['gphotos_client_id'], gphotos_client_2_id)
        self.assertEqual(bird_item['gphotos_media_item_id'], bird_gitem.id)

        # Test assert: check that the media items are linked to the albums in the db
        self.assertIn(
            f'{mongodb_client_1_id}:{dog_item["_id"]}', album_2010['media_item_ids']
        )
        self.assertIn(
            f'{mongodb_client_1_id}:{cat_item["_id"]}', album_2010['media_item_ids']
        )
        self.assertIn(
            f'{mongodb_client_1_id}:{fish_item["_id"]}', album_2009['media_item_ids']
        )
        self.assertIn(
            f'{mongodb_client_1_id}:{bird_item["_id"]}', album_2009['media_item_ids']
        )

    def test_backup_adding_items_to_existing_albums(self):
        # Test setup 1: Set up the config
        mongodb_client_1 = create_mock_mongo_client(1000)
        mongodb_client_2 = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client_1 = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        gphotos_client_2 = FakeGPhotosClient(gphotos_items_repo, 'sam@gmail.com')
        config = InMemoryConfig()
        mongodb_client_1_id = config.add_mongo_db_client(mongodb_client_1)
        config.add_mongo_db_client(mongodb_client_2)
        gphotos_client_1_id = config.add_gphotos_client(gphotos_client_1)
        gphotos_client_2_id = config.add_gphotos_client(gphotos_client_2)

        # Test setup 2: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphotos_client_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 3: Set up the existing albums
        root_album = albums_repo.create_album('', None, [], [])
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

        # Test setup 4: Add dog.png to Archives/Photos/2010
        gupload_token = gphotos_client_1.media_items().upload_photo(
            './Archives/Photos/2010/dog.png', 'dog.png'
        )
        gmedia_item_obj = gphotos_client_1.media_items().add_uploaded_photos_to_gphotos(
            [gupload_token]
        )
        media_item_obj = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_1_id),
                gphotos_media_item_id=gmedia_item_obj.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[media_item_obj.id]),
        )

        # Test setup 5: Build the objects for backup
        uploader = GPhotosMediaItemUploader(gphotos_client_repo)
        diffs_assigner = DiffsAssigner(config)
        backup = PhotosBackup(
            config, albums_repo, media_items_repo, uploader, diffs_assigner
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2010/cat.png',
                album_name="Archives/Photos/2010",
                file_name="cat.png",
                file_size=10,
                location=GpsLocation(latitude=-1, longitude=1),
            ),
        ]
        backup_results = backup.backup(diffs)

        # Test assert: check on backup results
        self.assertEqual(backup_results.num_media_items_added, 1)
        self.assertEqual(backup_results.num_media_items_deleted, 0)

        # Test assert: Check that there is a new gphotos item for cat.png
        gitems_1 = gphotos_client_1.media_items().search_for_media_items()
        gitems_2 = gphotos_client_2.media_items().search_for_media_items()
        self.assertEqual(len(gitems_1), 1)
        self.assertEqual(len(gitems_2), 1)
        cat_gitem = next(filter(lambda x: x.filename == 'cat.png', gitems_2))

        # Test assert: Check that there is a cat.png media item in the db
        mitems_1 = list(
            mongodb_client_1['sharded_google_photos']['media_items'].find({})
        )
        dog_mitem = next(filter(lambda x: x['file_name'] == 'dog.png', mitems_1))
        cat_mitem = next(filter(lambda x: x['file_name'] == 'cat.png', mitems_1))
        self.assertEqual(gphotos_client_2_id, cat_mitem['gphotos_client_id'])
        self.assertEqual(cat_gitem.id, cat_mitem['gphotos_media_item_id'])

        # Test assert: Check that no new albums have been made
        albums_1 = list(mongodb_client_1['sharded_google_photos']['albums'].find({}))
        self.assertEqual(len(albums_1), 4)

        # Test assert: Check that cat.png media item is attached to the 2010 album in
        # db, and dog.png is still kept
        album_2010_raw = next(filter(lambda x: x['name'] == '2010', albums_1))
        self.assertEqual(len(album_2010_raw['media_item_ids']), 2)
        self.assertIn(
            f'{mongodb_client_1_id}:{dog_mitem['_id']}',
            album_2010_raw['media_item_ids'],
        )
        self.assertIn(
            f'{mongodb_client_1_id}:{cat_mitem['_id']}',
            album_2010_raw['media_item_ids'],
        )

    def test_backup_deleted_one_item_on_album_with_two_items(self):
        # Test setup 1: Set up the essential objects
        mongodb_client_1 = create_mock_mongo_client(1000)
        mongodb_client_2 = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client_1 = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        gphotos_client_2 = FakeGPhotosClient(gphotos_items_repo, 'sam@gmail.com')
        config = InMemoryConfig()
        mongodb_client_1_id = config.add_mongo_db_client(mongodb_client_1)
        config.add_mongo_db_client(mongodb_client_2)
        gphotos_client_1_id = config.add_gphotos_client(gphotos_client_1)
        config.add_gphotos_client(gphotos_client_2)

        # Test setup 2: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphotos_client_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 3: Set up the existing albums
        root_album = albums_repo.create_album('', None, [], [])
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

        # Test setup 4: Add dog.png and cat.png to Archives/Photos/2010
        gdog_upload_token = gphotos_client_1.media_items().upload_photo(
            './Archives/Photos/2010/dog.png', 'dog.png'
        )
        gcat_upload_token = gphotos_client_2.media_items().upload_photo(
            './Archives/Photos/2010/cat.png', 'cat.png'
        )
        media_items_results_1 = (
            gphotos_client_1.media_items().add_uploaded_photos_to_gphotos(
                [gdog_upload_token]
            )
        )
        media_items_results_2 = (
            gphotos_client_2.media_items().add_uploaded_photos_to_gphotos(
                [gcat_upload_token]
            )
        )
        dog_mitem_obj = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_1_id),
                gphotos_media_item_id=media_items_results_1.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        cat_mitem_obj = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.png',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_1_id),
                gphotos_media_item_id=media_items_results_2.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[dog_mitem_obj.id, cat_mitem_obj.id]),
        )

        # Test setup 5: Build the objects for backup
        uploader = GPhotosMediaItemUploader(gphotos_client_repo)
        diffs_assigner = DiffsAssigner(config)
        backup = PhotosBackup(
            config, albums_repo, media_items_repo, uploader, diffs_assigner
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='-',
                file_path='./Archives/Photos/2010/cat.png',
                album_name="Archives/Photos/2010",
                file_name="cat.png",
                file_size=10,
                location=GpsLocation(latitude=-1, longitude=1),
            ),
        ]
        backup_results = backup.backup(diffs)

        # Test assert: check on backup results
        self.assertEqual(backup_results.num_media_items_added, 0)
        self.assertEqual(backup_results.num_media_items_deleted, 1)

        # Test assert: Check that there is dog.png but no cat.png media item in the db
        mitems_1 = list(
            mongodb_client_1['sharded_google_photos']['media_items'].find({})
        )
        dog_mitem = next(filter(lambda x: x['file_name'] == 'dog.png', mitems_1))
        self.assertEqual(
            list(filter(lambda x: x['file_name'] == 'cat.png', mitems_1)), []
        )

        # Test assert: Check that no new albums have been made
        albums_1 = list(mongodb_client_1['sharded_google_photos']['albums'].find({}))
        self.assertEqual(len(albums_1), 4)

        # Test assert: Check that cat.png is removed from album and dog.png is kept
        album_2010_raw = next(filter(lambda x: x['name'] == '2010', albums_1))
        self.assertEqual(len(album_2010_raw['media_item_ids']), 1)
        self.assertIn(
            f'{mongodb_client_1_id}:{dog_mitem['_id']}',
            album_2010_raw['media_item_ids'],
        )

    def test_backup_pruning_1(self):
        # Test setup 1: Build the config
        mongodb_client = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        config = InMemoryConfig()
        config.add_mongo_db_client(mongodb_client)
        gphotos_client_id = config.add_gphotos_client(gphotos_client)

        # Test setup 2: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphotos_client_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 3: Set up the existing albums
        root_album = albums_repo.create_album('', None, [], [])
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

        # Test setup 4: Add dog.png to Archives/Photos/2010
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.png', 'dog.png'
        )
        media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [dog_upload_token]
            )
        )
        media_item_obj = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[media_item_obj.id]),
        )

        # Test setup 5: Build the objects for backup
        uploader = GPhotosMediaItemUploader(gphotos_client_repo)
        diffs_assigner = DiffsAssigner(config)
        backup = PhotosBackup(
            config, albums_repo, media_items_repo, uploader, diffs_assigner
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='-',
                file_path='./Archives/Photos/2010/dog.png',
                album_name="Archives/Photos/2010",
                file_name="dog.png",
                file_size=10,
                location=GpsLocation(latitude=-1, longitude=1),
            ),
        ]
        backup_results = backup.backup(diffs)

        # Test assert: check that there's no media item
        media_items = media_items_repo.get_all_media_items()
        self.assertEqual(len(media_items), 0)

        # Test assert: check on backup results
        self.assertEqual(backup_results.num_media_items_added, 0)
        self.assertEqual(backup_results.num_media_items_deleted, 1)
        self.assertEqual(backup_results.num_albums_created, 0)
        self.assertEqual(backup_results.num_albums_deleted, 3)

        # Test assert: Check that only the root album exists
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 1)

        # Test assert: Check that root albums is updated correctly
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(len(albums[0].child_album_ids), 0)
        self.assertEqual(len(albums[0].media_item_ids), 0)
        self.assertEqual(albums[0].parent_album_id, None)

    def test_backup_pruning_2(self):
        # Test setup 1: Build the config
        mongodb_client = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        config = InMemoryConfig()
        config.add_mongo_db_client(mongodb_client)
        gphotos_client_id = config.add_gphotos_client(gphotos_client)

        # Test setup 2: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphotos_client_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 3: Set up the existing albums
        root_album = albums_repo.create_album('', None, [], [])
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

        # Test setup 4: Add dog.png to Archives/Photos/2010 and cat.png to Archives/
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.png', 'dog.png'
        )
        cat_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/cat.png', 'cat.png'
        )
        dog_media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [dog_upload_token]
            )
        )
        cat_media_items_results = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [cat_upload_token]
            )
        )
        dog_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=dog_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        cat_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.png',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=cat_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[dog_media_item.id]),
        )
        albums_repo.update_album(
            archives_album.id,
            UpdatedAlbumFields(new_media_item_ids=[cat_media_item.id]),
        )

        # Test setup 5: Build the objects for backup
        uploader = GPhotosMediaItemUploader(gphotos_client_repo)
        diffs_assigner = DiffsAssigner(config)
        backup = PhotosBackup(
            config, albums_repo, media_items_repo, uploader, diffs_assigner
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='-',
                file_path='./Archives/Photos/2010/dog.png',
                album_name="Archives/Photos/2010",
                file_name="dog.png",
                file_size=10,
                location=GpsLocation(latitude=-1, longitude=1),
            ),
        ]
        backup_results = backup.backup(diffs)

        # Test assert: check that there's only one media item
        media_items = media_items_repo.get_all_media_items()
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].file_name, 'cat.png')

        # Test assert: check on backup results
        self.assertEqual(backup_results.num_media_items_added, 0)
        self.assertEqual(backup_results.num_media_items_deleted, 1)
        self.assertEqual(backup_results.num_albums_created, 0)
        self.assertEqual(backup_results.num_albums_deleted, 2)

        # Test assert: Check that only the root/Archives album exists
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)

        # Test assert: Check that root album is updated correctly
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].child_album_ids, [albums[1].id])
        self.assertEqual(albums[0].media_item_ids, [])
        self.assertEqual(albums[0].parent_album_id, None)

        # Test assert: Check that archives album is updated correctly
        self.assertEqual(albums[1].id, archives_album.id)
        self.assertEqual(albums[1].child_album_ids, [])
        self.assertEqual(albums[1].media_item_ids, [cat_media_item.id])
        self.assertEqual(albums[1].parent_album_id, root_album.id)

    def test_backup_pruning_3(self):
        # Test setup 1: Build the config
        mongodb_client = create_mock_mongo_client(1000)
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        config = InMemoryConfig()
        config.add_mongo_db_client(mongodb_client)
        gphotos_client_id = config.add_gphotos_client(gphotos_client)

        # Test setup 2: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphotos_client_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 3: Set up the existing albums
        root_album = albums_repo.create_album('', None, [], [])
        public_album = albums_repo.create_album('Public', root_album.id, [], [])
        archives_album = albums_repo.create_album('Archives', root_album.id, [], [])
        photos_album = albums_repo.create_album('Photos', archives_album.id, [], [])
        album_2010 = albums_repo.create_album('2010', photos_album.id, [], [])
        config.set_root_album_id(root_album.id)
        albums_repo.update_album(
            root_album.id,
            UpdatedAlbumFields(
                new_child_album_ids=[archives_album.id, public_album.id]
            ),
        )
        albums_repo.update_album(
            archives_album.id,
            UpdatedAlbumFields(new_child_album_ids=[photos_album.id]),
        )
        albums_repo.update_album(
            photos_album.id,
            UpdatedAlbumFields(new_child_album_ids=[album_2010.id]),
        )

        # Test setup 4: Add dog.png to Archives/Photos/2010 and cat.png to Public/
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.png', 'dog.png'
        )
        cat_upload_token = gphotos_client.media_items().upload_photo(
            './Public/cat.png', 'cat.png'
        )
        media_items_results_1 = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [dog_upload_token]
            )
        )
        media_items_results_2 = (
            gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [cat_upload_token]
            )
        )
        dog_media_item_obj = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=media_items_results_1.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        cat_media_item_obj = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.png',
                hash_code=None,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=media_items_results_2.newMediaItemResults[
                    0
                ].mediaItem.id,
            )
        )
        albums_repo.update_album(
            album_2010.id,
            UpdatedAlbumFields(new_media_item_ids=[dog_media_item_obj.id]),
        )
        albums_repo.update_album(
            public_album.id,
            UpdatedAlbumFields(new_media_item_ids=[cat_media_item_obj.id]),
        )

        # Test setup 5: Build the objects for backup
        uploader = GPhotosMediaItemUploader(gphotos_client_repo)
        diffs_assigner = DiffsAssigner(config)
        backup = PhotosBackup(
            config, albums_repo, media_items_repo, uploader, diffs_assigner
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='-',
                file_path='./Archives/Photos/2010/dog.png',
                album_name="Archives/Photos/2010",
                file_name="dog.png",
                file_size=10,
                location=GpsLocation(latitude=-1, longitude=1),
            ),
        ]
        backup_results = backup.backup(diffs)

        # Test assert: check that there's only one media item
        media_items = media_items_repo.get_all_media_items()
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].file_name, 'cat.png')

        # Test assert: check on backup results
        self.assertEqual(backup_results.num_media_items_added, 0)
        self.assertEqual(backup_results.num_media_items_deleted, 1)
        self.assertEqual(backup_results.num_albums_created, 0)
        self.assertEqual(backup_results.num_albums_deleted, 3)

        # Test assert: Check that only the root/Archives album exists
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)

        # Test assert: Check that root album is updated correctly
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].child_album_ids, [albums[1].id])
        self.assertEqual(albums[0].media_item_ids, [])
        self.assertEqual(albums[0].parent_album_id, None)

        # Test assert: Check that archives album is updated correctly
        self.assertEqual(albums[1].id, public_album.id)
        self.assertEqual(albums[1].child_album_ids, [])
        self.assertEqual(albums[1].media_item_ids, [cat_media_item_obj.id])
        self.assertEqual(albums[1].parent_album_id, root_album.id)
