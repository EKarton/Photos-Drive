from datetime import datetime, timezone
from bson import Binary
from bson.objectid import ObjectId
from photos_drive.shared.llm.models.testing.fake_image_embedder import FAKE_EMBEDDING
from unittest_parametrize import parametrize
from unittest_parametrize import ParametrizedTestCase

from photos_drive.shared.maps.mongodb.map_cells_repository_impl import (
    MapCellsRepositoryImpl,
)
from photos_drive.shared.config.inmemory_config import InMemoryConfig
from photos_drive.shared.blob_store.gphotos.testing import (
    FakeGPhotosClient,
    FakeItemsRepository,
)
from photos_drive.shared.metadata.mongodb.albums_repository_impl import (
    AlbumsRepositoryImpl,
)
from photos_drive.shared.metadata.mongodb.media_items_repository_impl import (
    MediaItemsRepositoryImpl,
)
from photos_drive.shared.metadata.album_id import album_id_to_string
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.media_items_repository import (
    CreateMediaItemRequest,
)
from photos_drive.shared.metadata.media_items import GpsLocation
from photos_drive.shared.blob_store.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from photos_drive.backup.backup_photos import PhotosBackup
from photos_drive.backup.processed_diffs import ProcessedDiff
from photos_drive.shared.metadata.mongodb.testing import (
    create_mock_mongo_client,
)

parametrize_use_parallel_uploads = parametrize(
    "use_parallel_uploads",
    [(True,), (False,)],
)

MOCK_FILE_HASH = b'\x8a\x19\xdd\xdeg\xdd\x96\xf2'

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0, tzinfo=timezone.utc)


class TestPhotosBackup(ParametrizedTestCase):

    @parametrize_use_parallel_uploads
    def test_backup_adding_items_to_new_db(self, use_parallel_uploads: bool):
        # Test setup 1: Build the wrapper objects
        config = InMemoryConfig()

        mongodb_client_1_id = ObjectId()
        mongodb_client_2_id = ObjectId()
        mongodb_client_1 = create_mock_mongo_client(1000)
        mongodb_client_2 = create_mock_mongo_client(1000)
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(mongodb_client_1_id, mongodb_client_1)
        mongodb_clients_repo.add_mongodb_client(mongodb_client_2_id, mongodb_client_2)

        gphotos_client_1_id = ObjectId()
        gphotos_client_2_id = ObjectId()
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client_1 = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        gphotos_client_2 = FakeGPhotosClient(gphotos_items_repo, 'sam@gmail.com')
        gphotos_client_repo = GPhotosClientsRepository()
        gphotos_client_repo.add_gphotos_client(gphotos_client_1_id, gphotos_client_1)
        gphotos_client_repo.add_gphotos_client(gphotos_client_2_id, gphotos_client_2)

        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
        map_cells_repo = MapCellsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the root album
        root_album_obj = albums_repo.create_album('', None)
        config.set_root_album_id(root_album_obj.id)

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2010/dog.png',
                album_name="Archives/Photos/2010",
                file_name="dog.png",
                file_size=10,
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-1, longitude=1),
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2010/cat.png',
                album_name="Archives/Photos/2010",
                file_name="cat.png",
                file_size=10,
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-2, longitude=2),
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2009/fish.png',
                album_name="Archives/Photos/2009",
                file_name="fish.png",
                file_size=10,
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-3, longitude=3),
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2009/bird.png',
                album_name="Archives/Photos/2009",
                file_name="bird.png",
                file_size=10,
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-4, longitude=4),
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
        ]
        backup = PhotosBackup(
            config,
            albums_repo,
            media_items_repo,
            map_cells_repo,
            gphotos_client_repo,
            mongodb_clients_repo,
            parallelize_uploads=use_parallel_uploads,
        )
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
        albums_1 = list(mongodb_client_1['photos_drive']['albums'].find({}))
        albums_2 = list(mongodb_client_2['photos_drive']['albums'].find({}))

        self.assertEqual(len(albums_1), 5)
        self.assertEqual(len(albums_2), 0)
        root_album = next(filter(lambda x: x['name'] == '', albums_1))
        archives_album = next(filter(lambda x: x['name'] == 'Archives', albums_1))
        photos_album = next(filter(lambda x: x['name'] == 'Photos', albums_1))
        album_2009 = next(filter(lambda x: x['name'] == '2009', albums_1))
        album_2010 = next(filter(lambda x: x['name'] == '2010', albums_1))

        # Test assert: check on the root folder
        self.assertIsNone(root_album['parent_album_id'])

        # Test assert: check on the Archives folder and it's linked correctly
        self.assertIn(
            f'{root_album_obj.id.client_id}:{root_album_obj.id.object_id}',
            archives_album['parent_album_id'],
        )

        # Test assert: check on the Photos folder and it's linked correctly
        self.assertIn(
            f'{mongodb_client_1_id}:{archives_album['_id']}',
            photos_album['parent_album_id'],
        )

        # Test assert: check the media items in the db are made
        mitems_1 = list(mongodb_client_1['photos_drive']['media_items'].find({}))
        mitems_2 = list(mongodb_client_2['photos_drive']['media_items'].find({}))
        self.assertEqual(len(mitems_1), 4)
        self.assertEqual(len(mitems_2), 0)
        dog_item = next(filter(lambda x: x['file_name'] == 'dog.png', mitems_1))
        cat_item = next(filter(lambda x: x['file_name'] == 'cat.png', mitems_1))
        fish_item = next(filter(lambda x: x['file_name'] == 'fish.png', mitems_1))
        bird_item = next(filter(lambda x: x['file_name'] == 'bird.png', mitems_1))

        # Test assert: check that the media items in the db are linked to GPhotos
        self.assertEqual(dog_item['gphotos_client_id'], str(gphotos_client_1_id))
        self.assertEqual(dog_item['gphotos_media_item_id'], dog_gitem.id)
        self.assertEqual(cat_item['gphotos_client_id'], str(gphotos_client_2_id))
        self.assertEqual(cat_item['gphotos_media_item_id'], cat_gitem.id)
        self.assertEqual(fish_item['gphotos_client_id'], str(gphotos_client_1_id))
        self.assertEqual(fish_item['gphotos_media_item_id'], fish_gitem.id)
        self.assertEqual(bird_item['gphotos_client_id'], str(gphotos_client_2_id))
        self.assertEqual(bird_item['gphotos_media_item_id'], bird_gitem.id)

        # Test assert: check that the file hash is added to the media items
        self.assertEqual(dog_item['file_hash'], Binary(MOCK_FILE_HASH))
        self.assertEqual(cat_item['file_hash'], Binary(MOCK_FILE_HASH))
        self.assertEqual(fish_item['file_hash'], Binary(MOCK_FILE_HASH))
        self.assertEqual(bird_item['file_hash'], Binary(MOCK_FILE_HASH))

        # Test assert: check that the album IDs in the media items are correct
        self.assertEqual(
            dog_item['album_id'], f'{mongodb_client_1_id}:{album_2010['_id']}'
        )
        self.assertEqual(
            cat_item['album_id'], f'{mongodb_client_1_id}:{album_2010['_id']}'
        )
        self.assertEqual(
            fish_item['album_id'], f'{mongodb_client_1_id}:{album_2009['_id']}'
        )
        self.assertEqual(
            bird_item['album_id'], f'{mongodb_client_1_id}:{album_2009['_id']}'
        )

        # Test assert: check that the photos are added to map cells repository
        cell_items = list(
            mongodb_client_1['photos_drive']['map_cells'].find({})
        ) + list(mongodb_client_2['photos_drive']['map_cells'].find({}))
        dog_citem = list(
            filter(
                lambda x: x['media_item_id']
                == f'{mongodb_client_1_id}:{dog_item['_id']}',
                cell_items,
            )
        )
        cat_citem = list(
            filter(
                lambda x: x['media_item_id']
                == f'{mongodb_client_1_id}:{cat_item['_id']}',
                cell_items,
            )
        )
        fish_citem = list(
            filter(
                lambda x: x['media_item_id']
                == f'{mongodb_client_1_id}:{fish_item['_id']}',
                cell_items,
            )
        )
        bird_citem = list(
            filter(
                lambda x: x['media_item_id']
                == f'{mongodb_client_1_id}:{bird_item['_id']}',
                cell_items,
            )
        )
        self.assertEqual(len(dog_citem), 16)
        self.assertEqual(len(cat_citem), 16)
        self.assertEqual(len(fish_citem), 16)
        self.assertEqual(len(bird_citem), 16)
        self.assertEqual(len(cell_items), 16 * 4)

    @parametrize_use_parallel_uploads
    def test_backup_adding_items_to_existing_albums(self, use_parallel_uploads: bool):
        # Test setup 1: Set up the config
        config = InMemoryConfig()

        mongodb_client_1_id = ObjectId()
        mongodb_client_2_id = ObjectId()
        mongodb_client_1 = create_mock_mongo_client(1000)
        mongodb_client_2 = create_mock_mongo_client(1000)
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(mongodb_client_1_id, mongodb_client_1)
        mongodb_clients_repo.add_mongodb_client(mongodb_client_2_id, mongodb_client_2)

        gphotos_client_1_id = ObjectId()
        gphotos_client_2_id = ObjectId()
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client_1 = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        gphotos_client_2 = FakeGPhotosClient(gphotos_items_repo, 'sam@gmail.com')
        gphotos_client_repo = GPhotosClientsRepository()
        gphotos_client_repo.add_gphotos_client(gphotos_client_1_id, gphotos_client_1)
        gphotos_client_repo.add_gphotos_client(gphotos_client_2_id, gphotos_client_2)

        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
        map_cells_repo = MapCellsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the existing albums
        root_album = albums_repo.create_album('', None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos_album.id)
        config.set_root_album_id(root_album.id)

        # Test setup 3: Add dog.png to Archives/Photos/2010
        gupload_token = gphotos_client_1.media_items().upload_photo(
            './Archives/Photos/2010/dog.png', 'dog.png'
        )
        gmedia_item_obj = gphotos_client_1.media_items().add_uploaded_photos_to_gphotos(
            [gupload_token]
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_1_id),
                gphotos_media_item_id=gmedia_item_obj.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='+',
                file_path='./Archives/Photos/2010/cat.png',
                album_name="Archives/Photos/2010",
                file_name="cat.png",
                file_size=10,
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-1, longitude=1),
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
        ]
        backup = PhotosBackup(
            config,
            albums_repo,
            media_items_repo,
            map_cells_repo,
            gphotos_client_repo,
            mongodb_clients_repo,
            parallelize_uploads=use_parallel_uploads,
        )
        backup_results = backup.backup(diffs)

        # Test assert: check on backup results
        self.assertEqual(backup_results.num_media_items_added, 1)
        self.assertEqual(backup_results.num_media_items_deleted, 0)
        self.assertTrue(backup_results.total_elapsed_time > 0)

        # Test assert: Check that there is a new gphotos item for cat.png
        gitems_1 = gphotos_client_1.media_items().search_for_media_items()
        gitems_2 = gphotos_client_2.media_items().search_for_media_items()
        self.assertEqual(len(gitems_1), 1)
        self.assertEqual(len(gitems_2), 1)
        cat_gitem = next(filter(lambda x: x.filename == 'cat.png', gitems_2))

        # Test assert: Check that there are two media items
        mitems_1 = list(mongodb_client_1['photos_drive']['media_items'].find({}))
        self.assertEqual(len(mitems_1), 2)

        # Test assert: Check the new media item
        cat_mitem = next(filter(lambda x: x['file_name'] == 'cat.png', mitems_1))
        self.assertEqual(cat_mitem['gphotos_client_id'], str(gphotos_client_2_id))
        self.assertEqual(cat_mitem['gphotos_media_item_id'], cat_gitem.id)
        self.assertEqual(cat_mitem['file_hash'], Binary(MOCK_FILE_HASH))
        self.assertEqual(cat_mitem['album_id'], album_id_to_string(album_2010.id))

        # Test assert: Check the old media item
        dog_mitem = next(filter(lambda x: x['file_name'] == 'dog.png', mitems_1))
        self.assertEqual(dog_mitem['album_id'], album_id_to_string(album_2010.id))

        # Test assert: Check that no new albums have been made
        albums_1 = list(mongodb_client_1['photos_drive']['albums'].find({}))
        self.assertEqual(len(albums_1), 4)

        # Test assert: check that the new photo is added to map cells repository
        cell_items = list(
            mongodb_client_1['photos_drive']['map_cells'].find({})
        ) + list(mongodb_client_2['photos_drive']['map_cells'].find({}))
        cat_citem = list(
            filter(
                lambda x: x['media_item_id']
                == f'{mongodb_client_1_id}:{cat_mitem['_id']}',
                cell_items,
            )
        )
        self.assertEqual(len(cell_items), 16)
        self.assertEqual(len(cat_citem), 16)

    @parametrize_use_parallel_uploads
    def test_backup_deleted_one_item_on_album_with_two_items(
        self, use_parallel_uploads: bool
    ):
        # Test setup 1: Set up the config
        config = InMemoryConfig()

        mongodb_client_1_id = ObjectId()
        mongodb_client_2_id = ObjectId()
        mongodb_client_1 = create_mock_mongo_client(1000)
        mongodb_client_2 = create_mock_mongo_client(1000)
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(mongodb_client_1_id, mongodb_client_1)
        mongodb_clients_repo.add_mongodb_client(mongodb_client_2_id, mongodb_client_2)

        gphotos_client_1_id = ObjectId()
        gphotos_client_2_id = ObjectId()
        gphotos_items_repo = FakeItemsRepository()
        gphotos_client_1 = FakeGPhotosClient(gphotos_items_repo, 'bob@gmail.com')
        gphotos_client_2 = FakeGPhotosClient(gphotos_items_repo, 'sam@gmail.com')
        gphotos_client_repo = GPhotosClientsRepository()
        gphotos_client_repo.add_gphotos_client(gphotos_client_1_id, gphotos_client_1)
        gphotos_client_repo.add_gphotos_client(gphotos_client_2_id, gphotos_client_2)

        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
        map_cells_repo = MapCellsRepositoryImpl(mongodb_clients_repo)

        # Test setup 3: Set up the existing albums
        root_album = albums_repo.create_album('', None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos_album.id)
        config.set_root_album_id(root_album.id)

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
        dog_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-1, longitude=1),
                gphotos_client_id=ObjectId(gphotos_client_1_id),
                gphotos_media_item_id=media_items_results_1.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )
        map_cells_repo.add_media_item(dog_media_item)
        cat_media_item = media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.png',
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-1, longitude=1),
                gphotos_client_id=ObjectId(gphotos_client_1_id),
                gphotos_media_item_id=media_items_results_2.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )
        map_cells_repo.add_media_item(cat_media_item)

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='-',
                file_path='./Archives/Photos/2010/cat.png',
                album_name="Archives/Photos/2010",
                file_name="cat.png",
                file_size=10,
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-1, longitude=1),
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
        ]
        backup = PhotosBackup(
            config,
            albums_repo,
            media_items_repo,
            map_cells_repo,
            gphotos_client_repo,
            mongodb_clients_repo,
            parallelize_uploads=use_parallel_uploads,
        )
        backup_results = backup.backup(diffs)

        # Test assert: check on backup results
        self.assertEqual(backup_results.num_media_items_added, 0)
        self.assertEqual(backup_results.num_media_items_deleted, 1)
        self.assertTrue(backup_results.total_elapsed_time > 0)

        # Test assert: Check that there is dog.png but no cat.png media item in the db
        mitems_1 = list(mongodb_client_1['photos_drive']['media_items'].find({}))
        dog_mitem = next(filter(lambda x: x['file_name'] == 'dog.png', mitems_1))
        self.assertIsNotNone(dog_mitem)
        self.assertEqual(
            list(filter(lambda x: x['file_name'] == 'cat.png', mitems_1)), []
        )

        # Test assert: Check that no new albums have been made
        albums_1 = list(mongodb_client_1['photos_drive']['albums'].find({}))
        self.assertEqual(len(albums_1), 4)

        # Test assert: check that dog.png is still in the map cells repository
        cell_items = list(
            mongodb_client_1['photos_drive']['map_cells'].find({})
        ) + list(mongodb_client_2['photos_drive']['map_cells'].find({}))
        dog_citem = list(
            filter(
                lambda x: x['media_item_id']
                == f'{mongodb_client_1_id}:{dog_mitem['_id']}',
                cell_items,
            )
        )
        self.assertEqual(len(cell_items), 16)
        self.assertEqual(len(dog_citem), 16)

    @parametrize_use_parallel_uploads
    def test_backup_pruning_1(self, use_parallel_uploads: bool):
        # Test setup 1: Build the config
        config = InMemoryConfig()

        mongodb_client_id = ObjectId()
        mongodb_client = create_mock_mongo_client(1000)
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(mongodb_client_id, mongodb_client)

        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_client_repo = GPhotosClientsRepository()
        gphotos_client_repo.add_gphotos_client(gphotos_client_id, gphotos_client)

        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
        map_cells_repo = MapCellsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the existing albums
        root_album = albums_repo.create_album('', None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos_album.id)
        config.set_root_album_id(root_album.id)

        # Test setup 3: Add dog.png to Archives/Photos/2010
        dog_upload_token = gphotos_client.media_items().upload_photo(
            './Archives/Photos/2010/dog.png', 'dog.png'
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
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='-',
                file_path='./Archives/Photos/2010/dog.png',
                album_name="Archives/Photos/2010",
                file_name="dog.png",
                file_hash=MOCK_FILE_HASH,
                file_size=10,
                location=GpsLocation(latitude=-1, longitude=1),
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
        ]
        backup = PhotosBackup(
            config,
            albums_repo,
            media_items_repo,
            map_cells_repo,
            gphotos_client_repo,
            mongodb_clients_repo,
            parallelize_uploads=use_parallel_uploads,
        )
        backup_results = backup.backup(diffs)

        # Test assert: check that there's no media item
        media_items = media_items_repo.get_all_media_items()
        self.assertEqual(len(media_items), 0)

        # Test assert: check on backup results
        self.assertEqual(backup_results.num_media_items_added, 0)
        self.assertEqual(backup_results.num_media_items_deleted, 1)
        self.assertEqual(backup_results.num_albums_created, 0)
        self.assertEqual(backup_results.num_albums_deleted, 3)
        self.assertTrue(backup_results.total_elapsed_time > 0)

        # Test assert: Check that only the root album exists
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 1)

        # Test assert: Check that root albums is updated correctly
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].parent_album_id, None)

    @parametrize_use_parallel_uploads
    def test_backup_pruning_2(self, use_parallel_uploads: bool):
        # Test setup 1: Build the config
        config = InMemoryConfig()

        mongodb_client_id = ObjectId()
        mongodb_client = create_mock_mongo_client(1000)
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(mongodb_client_id, mongodb_client)

        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_client_repo = GPhotosClientsRepository()
        gphotos_client_repo.add_gphotos_client(gphotos_client_id, gphotos_client)

        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
        map_cells_repo = MapCellsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the existing albums
        root_album = albums_repo.create_album('', None)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos_album.id)
        config.set_root_album_id(root_album.id)

        # Test setup 3: Add dog.png to Archives/Photos/2010 and cat.png to Archives/
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
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=dog_media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
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
                album_id=archives_album.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='-',
                file_path='./Archives/Photos/2010/dog.png',
                album_name="Archives/Photos/2010",
                file_name="dog.png",
                file_size=10,
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-1, longitude=1),
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
        ]
        backup = PhotosBackup(
            config,
            albums_repo,
            media_items_repo,
            map_cells_repo,
            gphotos_client_repo,
            mongodb_clients_repo,
            parallelize_uploads=use_parallel_uploads,
        )
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
        self.assertTrue(backup_results.total_elapsed_time > 0)

        # Test assert: Check that only the root/Archives album exists
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)

        # Test assert: Check that root album is updated correctly
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].parent_album_id, None)

        # Test assert: Check that archives album is updated correctly
        self.assertEqual(albums[1].id, archives_album.id)
        self.assertEqual(albums[1].parent_album_id, root_album.id)

    @parametrize_use_parallel_uploads
    def test_backup_pruning_3(self, use_parallel_uploads: bool):
        # Test setup 1: Build the config
        config = InMemoryConfig()

        mongodb_client_id = ObjectId()
        mongodb_client = create_mock_mongo_client(1000)
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_clients_repo.add_mongodb_client(mongodb_client_id, mongodb_client)

        gphotos_client_id = ObjectId()
        gphotos_client = FakeGPhotosClient(FakeItemsRepository(), 'bob@gmail.com')
        gphotos_client_repo = GPhotosClientsRepository()
        gphotos_client_repo.add_gphotos_client(gphotos_client_id, gphotos_client)

        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
        map_cells_repo = MapCellsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the existing albums
        root_album = albums_repo.create_album('', None)
        public_album = albums_repo.create_album('Public', root_album.id)
        archives_album = albums_repo.create_album('Archives', root_album.id)
        photos_album = albums_repo.create_album('Photos', archives_album.id)
        album_2010 = albums_repo.create_album('2010', photos_album.id)
        config.set_root_album_id(root_album.id)

        # Test setup 3: Add dog.png to Archives/Photos/2010 and cat.png to Public/
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
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=media_items_results_1.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=album_2010.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )
        media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='cat.png',
                file_hash=MOCK_FILE_HASH,
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=media_items_results_2.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=public_album.id,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # Act: Upload a set of processed diffs
        diffs = [
            ProcessedDiff(
                modifier='-',
                file_path='./Archives/Photos/2010/dog.png',
                album_name="Archives/Photos/2010",
                file_name="dog.png",
                file_size=10,
                file_hash=MOCK_FILE_HASH,
                location=GpsLocation(latitude=-1, longitude=1),
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
        ]
        backup = PhotosBackup(
            config,
            albums_repo,
            media_items_repo,
            map_cells_repo,
            gphotos_client_repo,
            mongodb_clients_repo,
            parallelize_uploads=use_parallel_uploads,
        )
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
        self.assertTrue(backup_results.total_elapsed_time > 0)

        # Test assert: Check that only the root/Archives album exists
        albums = albums_repo.get_all_albums()
        self.assertEqual(len(albums), 2)

        # Test assert: Check that root album is updated correctly
        self.assertEqual(albums[0].id, root_album.id)
        self.assertEqual(albums[0].parent_album_id, None)

        # Test assert: Check that archives album is updated correctly
        self.assertEqual(albums[1].id, public_album.id)
        self.assertEqual(albums[1].parent_album_id, root_album.id)
