import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
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

        # Write initial config
        with open(self.temp_file_path, 'w') as f:
            f.write(
                """
[5f50c31e8a7d4b1c9c9b0b1a]
type = mongodb
name = TestMongoDB
connection_string = mongodb://localhost:27017

[5f50c31e8a7d4b1c9c9b0b1b]
type = gphotos
name = TestGPhotos
token = test_token
refresh_token = test_refresh_token
client_id = test_client_id
client_secret = test_client_secret
token_uri = https://oauth2.googleapis.com/token

[5f50c31e8a7d4b1c9c9b0b1c]
type = root_album
client_id = 5f50c31e8a7d4b1c9c9b0b1b
object_id = 5f50c31e8a7d4b1c9c9b0b1d
            """
            )

        self.config = ConfigFromFile(self.temp_file_path)

    def tearDown(self):
        os.unlink(self.temp_file_path)

    def test_get_mongo_db_clients__returns_all_mongodb_clients_in_config_file(self):
        clients = self.config.get_mongo_db_clients()

        self.assertEqual(len(clients), 1)
        self.assertEqual(str(clients[0][0]), "5f50c31e8a7d4b1c9c9b0b1a")
        self.assertIsInstance(clients[0][1], MongoClient)

    def test_add_mongo_db_client__adds_new_mongodb_client_to_config_file(self):
        new_id = self.config.add_mongo_db_client(
            "NewMongoDB", "mongodb://newhost:27017"
        )

        self.config.flush()
        with open(self.temp_file_path, 'r') as f:
            content = f.read()

            self.assertIn("NewMongoDB", content)
            self.assertIn("mongodb://newhost:27017", content)
            self.assertIn(str(new_id), content)

    def test_get_gphotos_clients__returns_gphotos_client_instances(self):
        clients = self.config.get_gphotos_clients()

        self.assertEqual(len(clients), 1)
        self.assertEqual(str(clients[0][0]), "5f50c31e8a7d4b1c9c9b0b1b")
        self.assertIsInstance(clients[0][1], GPhotosClientV2)

    def test_add_gphotos_client__creates_new_gphotos_client_instance(self):
        creds = Credentials(
            refresh_token="new_refresh_token",
            token="new_token",
            client_id="new_client_id",
            client_secret="new_client_secret",
            token_uri="https://new.token.uri",
        )
        client = GPhotosClientV2('NewGPhotos', AuthorizedSession(creds))

        new_id = self.config.add_gphotos_client(client)

        self.config.flush()
        with open(self.temp_file_path, 'r') as f:
            content = f.read()

            self.assertIn("NewGPhotos", content)
            self.assertIn(str(new_id), content)
            self.assertIn("new_refresh_token", content)
            self.assertIn("new_token", content)
            self.assertIn("new_client_id", content)
            self.assertIn("new_client_secret", content)
            self.assertIn("https://new.token.uri", content)

    def test_get_root_album_id__returns_root_album_id(self):
        root_album = self.config.get_root_album_id()

        self.assertEqual(str(root_album.client_id), "5f50c31e8a7d4b1c9c9b0b1b")
        self.assertEqual(str(root_album.object_id), "5f50c31e8a7d4b1c9c9b0b1d")

    def test_set_root_album_id__overwrites_root_album_id_and_saves_to_file(self):
        new_album_id = AlbumId(
            client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
            object_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1f"),
        )

        self.config.set_root_album_id(new_album_id)

        self.config.flush()
        with open(self.temp_file_path, 'r') as f:
            content = f.read()

            self.assertIn("5f50c31e8a7d4b1c9c9b0b1e", content)
            self.assertIn("5f50c31e8a7d4b1c9c9b0b1f", content)
