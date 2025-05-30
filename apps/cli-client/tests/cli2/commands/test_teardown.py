import os
import tempfile
import unittest
from unittest.mock import patch
from typer.testing import CliRunner
from bson import ObjectId

from sharded_photos_drive_cli_client.cli2.app import build_app
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
from sharded_photos_drive_cli_client.shared.mongodb.albums_repository import (
    AlbumsRepositoryImpl,
    UpdatedAlbumFields,
)
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.media_items_repository import (
    CreateMediaItemRequest,
    MediaItemsRepositoryImpl,
)
from sharded_photos_drive_cli_client.shared.mongodb.testing.mock_mongo_client import (
    create_mock_mongo_client,
)


class TestTeardownCli(unittest.TestCase):
    def setUp(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_client_id = ObjectId()
        mongodb_clients_repo.add_mongodb_client(
            mongodb_client_id, create_mock_mongo_client(1000)
        )
        gphotos_client_id = ObjectId()
        self.fake_gitems_repo = FakeItemsRepository()
        self.gphotos_client = FakeGPhotosClient(self.fake_gitems_repo, 'bob@gmail.com')
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, self.gphotos_client)

        self.albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        self.media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the root album
        self.root_album = self.albums_repo.create_album('', None, [])
        config = InMemoryConfig()
        config.set_root_album_id(self.root_album.id)

        # Test setup 3: Attach 'Archives' in root album but others not
        self.archives_album = self.albums_repo.create_album(
            'Archives', self.root_album.id, []
        )
        self.albums_repo.create_album('Photos', None, [])
        self.albums_repo.create_album('2010', None, [])
        self.albums_repo.create_album('2011', None, [])
        self.albums_repo.update_album(
            self.root_album.id,
            UpdatedAlbumFields(new_child_album_ids=[self.archives_album.id]),
        )

        # Test setup 4: Add an image to Archives
        dog_upload_token = self.gphotos_client.media_items().upload_photo(
            './Archives/dog.png', 'dog.png'
        )
        media_items_results = (
            self.gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [dog_upload_token]
            )
        )
        self.dog_media_item = self.media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name='dog.png',
                file_hash=b'\x8a\x19\xdd\xdeg\xdd\x96\xf2',
                location=None,
                gphotos_client_id=ObjectId(gphotos_client_id),
                gphotos_media_item_id=media_items_results.newMediaItemResults[
                    0
                ].mediaItem.id,
                album_id=self.archives_album.id,
            )
        )

        # Test setup: build fake config file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        with open(self.temp_file_path, 'w') as f:
            f.write(
                f'[{mongodb_client_id}]\n'
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
                + '\n'
                + f'[{gphotos_client_id}]\n'
                + 'type = gphotos_config\n'
                + 'name = TestGPhotos\n'
                + 'read_write_token = test_token\n'
                + 'read_write_refresh_token = test_refresh_token\n'
                + 'read_write_client_id = test_client_id\n'
                + 'read_write_client_secret = test_client_secret\n'
                + 'read_write_token_uri = https://oauth2.googleapis.com/token\n'
                + 'read_only_token = test_token_2\n'
                + 'read_only_refresh_token = test_refresh_token_2\n'
                + 'read_only_client_id = test_client_id_2\n'
                + 'read_only_client_secret = test_client_secret_2\n'
                + 'read_only_token_uri = https://oauth2.googleapis.com/token\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1c]\n'
                + 'type = root_album\n'
                + f'client_id = {self.root_album.id.client_id}\n'
                + f'object_id = {self.root_album.id.object_id}\n'
            )

        patch.object(
            MongoDbClientsRepository,
            'build_from_config',
            return_value=mongodb_clients_repo,
        ).start()

        patch.object(
            GPhotosClientsRepository,
            'build_from_config',
            return_value=gphotos_clients_repo,
        ).start()

    def tearDown(self):
        patch.stopall()
        os.unlink(self.temp_file_path)

    def test_teardown(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app, ["teardown", "--config-file", self.temp_file_path], input="Yes\n"
        )

        # Assert: check output
        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Do you want to delete everything this tool has ever created? (Y/N): ",
            result.stdout,
        )

        # Assert: check everything is deleted (except for root album)
        self.assertEqual(len(self.albums_repo.get_all_albums()), 1)
        self.assertEqual(len(self.media_items_repo.get_all_media_items()), 0)

        # Assert: all gmedia items moved to trash folder
        trash_album = next(
            filter(lambda x: x.title, self.gphotos_client.albums().list_albums())
        )
        all_media_items = self.gphotos_client.media_items().search_for_media_items()
        media_items_in_trash = self.gphotos_client.media_items().search_for_media_items(
            trash_album.id
        )
        self.assertEqual(len(all_media_items), 1)
        self.assertEqual(len(media_items_in_trash), 1)
