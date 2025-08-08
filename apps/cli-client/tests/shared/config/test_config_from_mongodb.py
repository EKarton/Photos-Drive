from typing import Dict, Mapping, cast
import unittest

from bson.objectid import ObjectId
from google.oauth2.credentials import Credentials

from photos_drive.shared.config.config import (
    AddGPhotosConfigRequest,
    AddMongoDbConfigRequest,
    MongoDbConfig,
    UpdateGPhotosConfigRequest,
    UpdateMongoDbConfigRequest,
)
from photos_drive.shared.config.config_from_mongodb import (
    ConfigFromMongoDb,
)
from photos_drive.shared.metadata.album_id import AlbumId
from photos_drive.shared.metadata.mongodb.testing import (
    create_mock_mongo_client,
)


class TestConfigFromMongoDb(unittest.TestCase):

    def setUp(self):
        self.mock_client = create_mock_mongo_client()
        self.config = ConfigFromMongoDb(self.mock_client)

    def tearDown(self):
        self.mock_client.close()

    def test_get_mongodb_configs(self):
        doc = self.mock_client["photos_drive"]["mongodb_configs"].insert_one(
            {
                "name": "bob@gmail.com",
                "read_write_connection_string": "mongodb://localhost:27017",
                "read_only_connection_string": "mongodb://localhost:27018",
            }
        )

        configs = self.config.get_mongodb_configs()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].id, doc.inserted_id)
        self.assertEqual(configs[0].name, "bob@gmail.com")
        self.assertEqual(
            configs[0].read_write_connection_string, "mongodb://localhost:27017"
        )
        self.assertEqual(
            configs[0].read_only_connection_string, "mongodb://localhost:27018"
        )

    def test_add_mongodb_config(self):
        request = AddMongoDbConfigRequest(
            name="Test Config",
            read_write_connection_string="mongodb://localhost:27017",
            read_only_connection_string="mongodb://localhost:27018",
        )

        result = self.config.add_mongodb_config(request)

        self.assertIsInstance(result, MongoDbConfig)
        self.assertIsInstance(result.id, ObjectId)
        self.assertEqual(result.name, request.name)
        self.assertEqual(
            result.read_write_connection_string, request.read_write_connection_string
        )
        self.assertEqual(
            result.read_only_connection_string, request.read_only_connection_string
        )

        inserted_doc = cast(
            Mapping,
            self.mock_client["photos_drive"]["mongodb_configs"].find_one(
                {"_id": result.id}
            ),
        )
        self.assertIsNotNone(inserted_doc)
        self.assertEqual(inserted_doc["name"], request.name)
        self.assertEqual(
            inserted_doc["read_write_connection_string"],
            request.read_write_connection_string,
        )
        self.assertEqual(
            inserted_doc["read_only_connection_string"],
            request.read_only_connection_string,
        )

    def test_update_mongodb_config(self):
        config_id = ObjectId()
        self.mock_client["photos_drive"]["mongodb_configs"].insert_one(
            {
                "_id": config_id,
                "name": "Original Name",
                "read_write_connection_string": "mongodb://original_rw",
                "read_only_connection_string": "mongodb://original_ro",
            }
        )

        request = UpdateMongoDbConfigRequest(
            id=config_id,
            new_name="Updated Name",
            new_read_write_connection_string="mongodb://updated_rw",
            new_read_only_connection_string="mongodb://updated_ro",
        )
        self.config.update_mongodb_config(request)

        updated_doc = cast(
            Mapping,
            self.mock_client["photos_drive"]["mongodb_configs"].find_one(
                {"_id": config_id}
            ),
        )
        self.assertEqual(updated_doc["name"], "Updated Name")
        self.assertEqual(
            updated_doc["read_write_connection_string"], "mongodb://updated_rw"
        )
        self.assertEqual(
            updated_doc["read_only_connection_string"], "mongodb://updated_ro"
        )

    def test_update_nonexistent_config(self):
        non_existent_id = ObjectId()
        request = UpdateMongoDbConfigRequest(id=non_existent_id, new_name="New Name")

        with self.assertRaisesRegex(ValueError, "Unable to update MongoDB config .*"):
            self.config.update_mongodb_config(request)

    def test_add_and_get_gphotos_configs(self):
        add_request = AddGPhotosConfigRequest(
            name="bob@gmail.com",
            read_write_credentials=Credentials(
                token="new_token_1",
                refresh_token="new_refresh_token_1",
                token_uri="https://new.token.uri",
                client_id="new_client_id_1",
                client_secret="new_client_secret_1",
            ),
            read_only_credentials=Credentials(
                token="new_token_2",
                refresh_token="new_refresh_token_2",
                token_uri="https://new.token.uri",
                client_id="new_client_id_2",
                client_secret="new_client_secret_2",
            ),
        )

        config = self.config.add_gphotos_config(add_request)
        retrieved_configs = self.config.get_gphotos_configs()

        self.assertEqual(config.name, add_request.name)
        self.assert_credentials_are_equal(
            config.read_write_credentials, add_request.read_write_credentials
        )
        self.assert_credentials_are_equal(
            config.read_only_credentials, add_request.read_only_credentials
        )
        self.assertEqual(config.id, retrieved_configs[0].id)
        self.assertEqual(config.name, retrieved_configs[0].name)
        self.assert_credentials_are_equal(
            config.read_write_credentials, retrieved_configs[0].read_write_credentials
        )
        self.assert_credentials_are_equal(
            config.read_only_credentials, retrieved_configs[0].read_only_credentials
        )

    def test_add_gphotos_config(self):
        add_request = AddGPhotosConfigRequest(
            name="bob@gmail.com",
            read_write_credentials=Credentials(
                token="new_token_1",
                refresh_token="new_refresh_token_1",
                token_uri="https://new.token.uri",
                client_id="new_client_id_1",
                client_secret="new_client_secret_1",
            ),
            read_only_credentials=Credentials(
                token="new_token_2",
                refresh_token="new_refresh_token_2",
                token_uri="https://new.token.uri",
                client_id="new_client_id_2",
                client_secret="new_client_secret_2",
            ),
        )
        config = self.config.add_gphotos_config(add_request)

        self.assertEqual(config.name, add_request.name)
        self.assert_credentials_are_equal(
            config.read_write_credentials, add_request.read_write_credentials
        )
        self.assert_credentials_are_equal(
            config.read_only_credentials, add_request.read_only_credentials
        )

    def test_get_gphotos_config(self):
        doc = self.mock_client["photos_drive"]["gphotos_configs"].insert_one(
            {
                "name": "bob@gmail.com",
                "read_write_credentials": {
                    "token": "new_token_1",
                    "refresh_token": "new_refresh_token_1",
                    "token_uri": "https://new.token.uri",
                    "client_id": "new_client_id_1",
                    "client_secret": "new_client_secret_1",
                },
                "read_only_credentials": {
                    "token": "new_token_2",
                    "refresh_token": "new_refresh_token_2",
                    "token_uri": "https://new.token.uri",
                    "client_id": "new_client_id_2",
                    "client_secret": "new_client_secret_2",
                },
            }
        )

        configs = self.config.get_gphotos_configs()

        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].id, doc.inserted_id)
        self.assertEqual(configs[0].name, "bob@gmail.com")
        self.assert_credentials_are_equal(
            configs[0].read_write_credentials,
            Credentials(
                token="new_token_1",
                refresh_token="new_refresh_token_1",
                token_uri="https://new.token.uri",
                client_id="new_client_id_1",
                client_secret="new_client_secret_1",
            ),
        )
        self.assert_credentials_are_equal(
            configs[0].read_only_credentials,
            Credentials(
                token="new_token_2",
                refresh_token="new_refresh_token_2",
                token_uri="https://new.token.uri",
                client_id="new_client_id_2",
                client_secret="new_client_secret_2",
            ),
        )

    def test_update_gphotos_config(self):
        doc = self.mock_client["photos_drive"]["gphotos_configs"].insert_one(
            {
                "name": "bob@gmail.com",
                "read_write_credentials": {
                    "token": "new_token_1",
                    "refresh_token": "new_refresh_token_1",
                    "token_uri": "https://new.token.uri",
                    "client_id": "new_client_id_1",
                    "client_secret": "new_client_secret_1",
                },
                "read_only_credentials": {
                    "token": "new_token_2",
                    "refresh_token": "new_refresh_token_2",
                    "token_uri": "https://new.token.uri",
                    "client_id": "new_client_id_2",
                    "client_secret": "new_client_secret_2",
                },
            }
        )

        request = UpdateGPhotosConfigRequest(
            id=doc.inserted_id,
            new_name='sam@gmail.com',
            new_read_write_credentials=Credentials(
                token="new_token_1b",
                refresh_token="new_refresh_token_1b",
                token_uri="https://new.token.uri",
                client_id="new_client_id_1b",
                client_secret="new_client_secret_1b",
            ),
            new_read_only_credentials=Credentials(
                token="new_token_2b",
                refresh_token="new_refresh_token_2b",
                token_uri="https://new.token.uri",
                client_id="new_client_id_2b",
                client_secret="new_client_secret_2b",
            ),
        )
        self.config.update_gphotos_config(request)

        new_doc = cast(
            Mapping,
            self.mock_client["photos_drive"]["gphotos_configs"].find_one(
                {"_id": doc.inserted_id}
            ),
        )
        self.assertEqual(new_doc['name'], cast(str, request.new_name))
        new_read_write_creds = cast(Credentials, request.new_read_write_credentials)
        self.assertEqual(
            new_doc['read_write_credentials'],
            {
                'token': new_read_write_creds.token,
                'refresh_token': new_read_write_creds.refresh_token,
                'token_uri': new_read_write_creds.token_uri,
                'client_id': new_read_write_creds.client_id,
                'client_secret': new_read_write_creds.client_secret,
            },
        )
        new_read_only_creds = cast(Credentials, request.new_read_only_credentials)
        self.assertEqual(
            new_doc['read_only_credentials'],
            {
                'token': new_read_only_creds.token,
                'refresh_token': new_read_only_creds.refresh_token,
                'token_uri': new_read_only_creds.token_uri,
                'client_id': new_read_only_creds.client_id,
                'client_secret': new_read_only_creds.client_secret,
            },
        )

    def test_update_gphotos_config_with_unknown_id(self):
        update_request = UpdateGPhotosConfigRequest(
            id=ObjectId("5f50c31e8a7d4b1c9c9b0b1c"),
            new_name='sam@gmail.com',
            new_read_write_credentials=Credentials(
                token="new_token_1b",
                refresh_token="new_refresh_token_1b",
                token_uri="https://new.token.uri",
                client_id="new_client_id_1b",
                client_secret="new_client_secret_1b",
            ),
            new_read_only_credentials=Credentials(
                token="new_token_2b",
                refresh_token="new_refresh_token_2b",
                token_uri="https://new.token.uri",
                client_id="new_client_id_2b",
                client_secret="new_client_secret_2b",
            ),
        )

        with self.assertRaisesRegex(ValueError, "Cannot find GPhotos config .*"):
            self.config.update_gphotos_config(update_request)

    def test_get_root_album_id(self):
        self.mock_client["photos_drive"]["root_album"].insert_one(
            {
                "client_id": ObjectId("5f50c31e8a7d4b1c9c9b0b1c"),
                "object_id": ObjectId("5f50c31e8a7d4b1c9c9b0b1d"),
            }
        )

        root_album = self.config.get_root_album_id()

        self.assertEqual(str(root_album.client_id), "5f50c31e8a7d4b1c9c9b0b1c")
        self.assertEqual(str(root_album.object_id), "5f50c31e8a7d4b1c9c9b0b1d")

    def test_get_root_album_id_with_no_root_album_id_set(self):
        with self.assertRaisesRegex(ValueError, 'No root album ID!'):
            self.config.get_root_album_id()

    def test_set_root_album_id(self):
        new_album_id = AlbumId(
            client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
            object_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1f"),
        )

        self.config.set_root_album_id(new_album_id)

        inserted_doc = cast(
            Dict, self.mock_client["photos_drive"]["root_album"].find_one()
        )
        self.assertIsNotNone(inserted_doc)
        self.assertEqual(str(inserted_doc["client_id"]), "5f50c31e8a7d4b1c9c9b0b1e")
        self.assertEqual(str(inserted_doc["object_id"]), "5f50c31e8a7d4b1c9c9b0b1f")

    def assert_credentials_are_equal(self, creds1: Credentials, creds2: Credentials):
        self.assertEqual(creds1.token, creds2.token)
        self.assertEqual(creds1.refresh_token, creds2.refresh_token)
        self.assertEqual(creds1.token_uri, creds2.token_uri)
        self.assertEqual(creds1.client_id, creds2.client_id)
        self.assertEqual(creds1.client_secret, creds2.client_secret)
