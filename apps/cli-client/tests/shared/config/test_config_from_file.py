import unittest
import tempfile
import os
from bson.objectid import ObjectId

from pymongo.mongo_client import MongoClient
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

from sharded_photos_drive_cli_client.shared.config.config_from_file import (
    ConfigFromFile,
)
from sharded_photos_drive_cli_client.shared.gphotos.client import GPhotosClientV2
from sharded_photos_drive_cli_client.shared.mongodb.albums import AlbumId


class TestConfigFromFile(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file_path)

    def test_get_mongo_db_clients(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb\n'
                + 'name = TestMongoDB\n'
                + 'connection_string = mongodb://localhost:27017\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
                + 'type = gphotos\n'
                + 'name = TestGPhotos\n'
                + 'token = test_token\n'
                + 'refresh_token = test_refresh_token\n'
                + 'client_id = test_client_id\n'
                + 'client_secret = test_client_secret\n'
                + 'token_uri = https://oauth2.googleapis.com/token\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1c]\n'
                + 'type = root_album\n'
                + 'client_id = 5f50c31e8a7d4b1c9c9b0b1b\n'
                + 'object_id = 5f50c31e8a7d4b1c9c9b0b1d\n'
            )

        config = ConfigFromFile(self.temp_file_path)
        clients = config.get_mongo_db_clients()

        self.assertEqual(len(clients), 1)
        self.assertEqual(str(clients[0][0]), "5f50c31e8a7d4b1c9c9b0b1a")
        self.assertIsInstance(clients[0][1], MongoClient)

    def test_add_mongo_db_client(self):
        config = ConfigFromFile(self.temp_file_path)
        new_id = config.add_mongo_db_client("NewMongoDB", "mongodb://newhost:27017")

        with open(self.temp_file_path, 'r') as f:
            content = f.read()

            self.assertIn("NewMongoDB", content)
            self.assertIn("mongodb://newhost:27017", content)
            self.assertIn(str(new_id), content)

    def test_get_gphotos_clients(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb\n'
                + 'name = TestMongoDB\n'
                + 'connection_string = mongodb://localhost:27017\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
                + 'type = gphotos\n'
                + 'name = TestGPhotos\n'
                + 'token = test_token\n'
                + 'refresh_token = test_refresh_token\n'
                + 'client_id = test_client_id\n'
                + 'client_secret = test_client_secret\n'
                + 'token_uri = https://oauth2.googleapis.com/token\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1c]\n'
                + 'type = root_album\n'
                + 'client_id = 5f50c31e8a7d4b1c9c9b0b1b\n'
                + 'object_id = 5f50c31e8a7d4b1c9c9b0b1d\n'
            )

        config = ConfigFromFile(self.temp_file_path)
        clients = config.get_gphotos_clients()

        self.assertEqual(len(clients), 1)
        self.assertEqual(str(clients[0][0]), "5f50c31e8a7d4b1c9c9b0b1b")
        self.assertIsInstance(clients[0][1], GPhotosClientV2)

    def test_add_gphotos_client(self):
        creds = Credentials(
            refresh_token="new_refresh_token",
            token="new_token",
            client_id="new_client_id",
            client_secret="new_client_secret",
            token_uri="https://new.token.uri",
        )
        client = GPhotosClientV2('NewGPhotos', AuthorizedSession(creds))

        config = ConfigFromFile(self.temp_file_path)
        new_id = config.add_gphotos_client(client)

        with open(self.temp_file_path, 'r') as f:
            content = f.read()

            self.assertIn("NewGPhotos", content)
            self.assertIn(str(new_id), content)
            self.assertIn("new_refresh_token", content)
            self.assertIn("new_token", content)
            self.assertIn("new_client_id", content)
            self.assertIn("new_client_secret", content)
            self.assertIn("https://new.token.uri", content)

    def test_get_root_album_id(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb\n'
                + 'name = TestMongoDB\n'
                + 'connection_string = mongodb://localhost:27017\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
                + 'type = gphotos\n'
                + 'name = TestGPhotos\n'
                + 'token = test_token\n'
                + 'refresh_token = test_refresh_token\n'
                + 'client_id = test_client_id\n'
                + 'client_secret = test_client_secret\n'
                + 'token_uri = https://oauth2.googleapis.com/token\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1c]\n'
                + 'type = root_album\n'
                + 'client_id = 5f50c31e8a7d4b1c9c9b0b1b\n'
                + 'object_id = 5f50c31e8a7d4b1c9c9b0b1d\n'
            )

        config = ConfigFromFile(self.temp_file_path)
        root_album = config.get_root_album_id()

        self.assertEqual(str(root_album.client_id), "5f50c31e8a7d4b1c9c9b0b1b")
        self.assertEqual(str(root_album.object_id), "5f50c31e8a7d4b1c9c9b0b1d")

    def test_get_root_album_id__no_root_id_in_file(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb\n'
                + 'name = TestMongoDB\n'
                + 'connection_string = mongodb://localhost:27017\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
                + 'type = gphotos\n'
                + 'name = TestGPhotos\n'
                + 'token = test_token\n'
                + 'refresh_token = test_refresh_token\n'
                + 'client_id = test_client_id\n'
                + 'client_secret = test_client_secret\n'
                + 'token_uri = https://oauth2.googleapis.com/token\n',
            )

        config = ConfigFromFile(self.temp_file_path)
        with self.assertRaisesRegex(ValueError, "Cannot find root album"):
            config.get_root_album_id()

    def test_set_root_album_id(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb\n'
                + 'name = TestMongoDB\n'
                + 'connection_string = mongodb://localhost:27017\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
                + 'type = gphotos\n'
                + 'name = TestGPhotos\n'
                + 'token = test_token\n'
                + 'refresh_token = test_refresh_token\n'
                + 'client_id = test_client_id\n'
                + 'client_secret = test_client_secret\n'
                + 'token_uri = https://oauth2.googleapis.com/token\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1c]\n'
                + 'type = root_album\n'
                + 'client_id = 5f50c31e8a7d4b1c9c9b0b1b\n'
                + 'object_id = 5f50c31e8a7d4b1c9c9b0b1d\n'
            )

        new_album_id = AlbumId(
            client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
            object_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1f"),
        )
        config = ConfigFromFile(self.temp_file_path)
        config.set_root_album_id(new_album_id)

        with open(self.temp_file_path, 'r') as f:
            content = f.read()
            self.assertIn("5f50c31e8a7d4b1c9c9b0b1e", content)
            self.assertIn("5f50c31e8a7d4b1c9c9b0b1f", content)
