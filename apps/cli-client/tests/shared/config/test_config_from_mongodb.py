from typing import Dict, cast
import unittest
from bson.objectid import ObjectId

from pymongo.mongo_client import MongoClient
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

from sharded_photos_drive_cli_client.shared.config.config_from_mongodb import (
    ConfigFromMongoDb,
)
from sharded_photos_drive_cli_client.shared.gphotos.client import GPhotosClientV2
from sharded_photos_drive_cli_client.shared.mongodb.albums import AlbumId
from sharded_photos_drive_cli_client.shared.mongodb.testing.mock_mongo_client import (
    create_mock_mongo_client,
)


class TestConfigFromMongoDb(unittest.TestCase):

    def setUp(self):
        self.mock_client = create_mock_mongo_client()
        self.config = ConfigFromMongoDb(self.mock_client)

    def tearDown(self):
        self.mock_client.close()

    def test_get_mongo_db_clients__returns_list_of_mongodb_clients(self):
        self.mock_client["sharded_google_photos"]["mongodb_clients"].insert_one(
            {
                "_id": ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
                "name": "TestMongoDB",
                "connection_string": "mongodb://localhost:27017",
            }
        )

        clients = self.config.get_mongo_db_clients()

        self.assertEqual(len(clients), 1)
        self.assertEqual(str(clients[0][0]), "5f50c31e8a7d4b1c9c9b0b1a")
        self.assertIsInstance(clients[0][1], MongoClient)

    def test_add_mongo_db_client__adds_new_mongodb_client_in_database(self):
        new_id = self.config.add_mongo_db_client(
            "NewMongoDB", "mongodb://newhost:27017"
        )

        inserted_doc = cast(
            Dict,
            self.mock_client["sharded_google_photos"]["mongodb_clients"].find_one(
                {"_id": new_id}
            ),
        )
        self.assertIsNotNone(inserted_doc)
        self.assertEqual(inserted_doc["name"], "NewMongoDB")
        self.assertEqual(inserted_doc["connection_string"], "mongodb://newhost:27017")

    def test_get_gphotos_clients__returns_list_of_gphotos_clients(self):
        self.mock_client["sharded_google_photos"]["gphotos_clients"].insert_one(
            {
                "_id": ObjectId("5f50c31e8a7d4b1c9c9b0b1b"),
                "name": "TestGPhotos",
                "token": "test_token",
                "refresh_token": "test_refresh_token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }
        )

        clients = self.config.get_gphotos_clients()

        self.assertEqual(len(clients), 1)
        self.assertEqual(str(clients[0][0]), "5f50c31e8a7d4b1c9c9b0b1b")
        self.assertIsInstance(clients[0][1], GPhotosClientV2)

    def test_add_gphotos_client__adds_gphotos_client_into_mongodb(self):
        creds = Credentials(
            token="new_token",
            refresh_token="new_refresh_token",
            token_uri="https://new.token.uri",
            client_id="new_client_id",
            client_secret="new_client_secret",
        )
        client = GPhotosClientV2('NewGPhotos', AuthorizedSession(creds))

        new_id = self.config.add_gphotos_client(client)

        inserted_doc = cast(
            Dict,
            self.mock_client["sharded_google_photos"]["gphotos_clients"].find_one(
                {"_id": new_id}
            ),
        )
        self.assertIsNotNone(inserted_doc)
        self.assertEqual(inserted_doc["name"], "NewGPhotos")
        self.assertEqual(inserted_doc["token"], "new_token")
        self.assertEqual(inserted_doc["refresh_token"], "new_refresh_token")
        self.assertEqual(inserted_doc["token_uri"], "https://new.token.uri")
        self.assertEqual(inserted_doc["client_id"], "new_client_id")
        self.assertEqual(inserted_doc["client_secret"], "new_client_secret")

    def test_get_root_album_id__returns_root_album_id_from_database(self):
        self.mock_client["sharded_google_photos"]["root_album"].insert_one(
            {
                "client_id": ObjectId("5f50c31e8a7d4b1c9c9b0b1c"),
                "object_id": ObjectId("5f50c31e8a7d4b1c9c9b0b1d"),
            }
        )

        root_album = self.config.get_root_album_id()

        self.assertEqual(str(root_album.client_id), "5f50c31e8a7d4b1c9c9b0b1c")
        self.assertEqual(str(root_album.object_id), "5f50c31e8a7d4b1c9c9b0b1d")

    def test_get_root_album_id__no_root_album_id_set__throws_error(self):
        with self.assertRaisesRegex(ValueError, 'No root album ID!'):
            self.config.get_root_album_id()

    def test_set_root_album_id__sets_root_album_id_in_database(self):
        new_album_id = AlbumId(
            client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
            object_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1f"),
        )

        self.config.set_root_album_id(new_album_id)

        inserted_doc = cast(
            Dict, self.mock_client["sharded_google_photos"]["root_album"].find_one()
        )
        self.assertIsNotNone(inserted_doc)
        self.assertEqual(str(inserted_doc["client_id"]), "5f50c31e8a7d4b1c9c9b0b1e")
        self.assertEqual(str(inserted_doc["object_id"]), "5f50c31e8a7d4b1c9c9b0b1f")
