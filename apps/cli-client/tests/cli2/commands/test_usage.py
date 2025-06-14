import os
import tempfile
from unittest.mock import patch
import unittest
from bson import ObjectId
from pymongo import MongoClient
from typer.testing import CliRunner

from sharded_photos_drive_cli_client.cli2.app import build_app
from sharded_photos_drive_cli_client.shared.blob_store.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from sharded_photos_drive_cli_client.shared.blob_store.gphotos.testing.fake_client import (
    FakeGPhotosClient,
)
from sharded_photos_drive_cli_client.shared.blob_store.gphotos.testing import (
    FakeItemsRepository,
)
from sharded_photos_drive_cli_client.shared.metadata.mongodb.albums_repository_impl import (
    AlbumsRepositoryImpl,
)
from sharded_photos_drive_cli_client.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from sharded_photos_drive_cli_client.shared.metadata.mongodb.testing.mock_mongo_client import (
    create_mock_mongo_client,
)


class TestUsageCli(unittest.TestCase):
    def setUp(self):
        # Test setup 1: Build the wrapper objects
        mongodb_clients_repo = MongoDbClientsRepository()
        mongodb_client_id = ObjectId()
        mongodb_client = create_mock_mongo_client(1000)
        mongodb_clients_repo.add_mongodb_client(mongodb_client_id, mongodb_client)
        gphotos_client_id = ObjectId()
        self.gphotos_client = FakeGPhotosClient(
            FakeItemsRepository(), 'bob@gmail.com', 1000
        )
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, self.gphotos_client)

        self.albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)

        # Test setup 2: Set up the root album
        self.root_album = self.albums_repo.create_album('', None, [])

        # Test setup 5: build fake config file
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

        patch.object(MongoClient, '__init__', return_value=None).start()
        patch.object(MongoClient, '__new__', return_value=mongodb_client).start()

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

    def test_usage(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["usage", "--config-file", self.temp_file_path])

        # Assert: check output
        self.assertIsNone(result.exception)
        self.assertEqual(result.exit_code, 0)
