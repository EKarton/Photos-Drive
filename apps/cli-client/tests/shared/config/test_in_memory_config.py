import unittest
from bson.objectid import ObjectId
from mongomock import MongoClient
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

from sharded_photos_drive_cli_client.shared.gphotos.client import GPhotosClientV2
from sharded_photos_drive_cli_client.shared.config.inmemory_config import InMemoryConfig
from sharded_photos_drive_cli_client.shared.mongodb.albums import AlbumId


class TestInMemoryConfig(unittest.TestCase):
    def setUp(self):
        self.config = InMemoryConfig()

    def test_add_mongo_db_client(self):
        connection_string = "mongodb://localhost:27017"
        client_id = self.config.add_mongo_db_client(MongoClient(connection_string))

        clients = self.config.get_mongo_db_clients()

        self.assertEqual(len(clients), 1)
        self.assertIsInstance(clients[0][1], MongoClient)
        self.assertEqual(clients[0][0], ObjectId(client_id))

    def test_add_gphotos_client(self):
        creds = Credentials(
            refresh_token="new_refresh_token",
            token="new_token",
            client_id="new_client_id",
            client_secret="new_client_secret",
            token_uri="https://new.token.uri",
        )
        gphotos_client = GPhotosClientV2('bob@gmail.com', AuthorizedSession(creds))

        client_id = self.config.add_gphotos_client(gphotos_client)

        clients = self.config.get_gphotos_clients()
        self.assertEqual(len(clients), 1)
        self.assertIsInstance(clients[0][1], GPhotosClientV2)
        self.assertEqual(clients[0][0], ObjectId(client_id))

    def test_set_and_get_root_album_id(self):
        album_id = AlbumId(client_id=ObjectId(), object_id=ObjectId())
        self.config.set_root_album_id(album_id)

        self.assertEqual(self.config.get_root_album_id(), album_id)

    def test_get_root_album_id_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "Cannot find root album"):
            self.config.get_root_album_id()

    def test_add_mongo_db_client__adds_mongo_db_to_config(self):
        connection_string = "mongodb://localhost:27017"
        client_id = self.config.add_mongo_db_client(connection_string)

        clients = self.config.get_mongo_db_clients()
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0][0], ObjectId(client_id))
