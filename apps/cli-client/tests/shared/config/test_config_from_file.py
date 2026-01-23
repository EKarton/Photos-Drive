import os
import tempfile
import unittest

from bson.objectid import ObjectId
from google.oauth2.credentials import Credentials

from photos_drive.shared.config.config import (
    AddGPhotosConfigRequest,
    AddMongoDbConfigRequest,
    UpdateGPhotosConfigRequest,
    UpdateMongoDbConfigRequest,
)
from photos_drive.shared.config.config_from_file import (
    ConfigFromFile,
)
from photos_drive.shared.metadata.albums.album_id import AlbumId


class TestConfigFromFile(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file_path)

    def test_get_mongodb_configs(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
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
                + 'client_id = 5f50c31e8a7d4b1c9c9b0b1b\n'
                + 'object_id = 5f50c31e8a7d4b1c9c9b0b1d\n'
            )

        config = ConfigFromFile(self.temp_file_path)
        clients = config.get_mongodb_configs()

        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0].id, ObjectId("5f50c31e8a7d4b1c9c9b0b1a"))
        self.assertEqual(clients[0].name, "TestMongoDB")
        self.assertEqual(
            clients[0].read_write_connection_string, "mongodb://localhost:27017"
        )
        self.assertEqual(
            clients[0].read_only_connection_string, "mongodb://localhost:27016"
        )

    def test_add_mongodb_config(self):
        request = AddMongoDbConfigRequest(
            name="bob@gmail.com",
            read_write_connection_string="mongodb://localhost:27017",
            read_only_connection_string="mongodb://localhost:27016",
        )
        config_file = ConfigFromFile(self.temp_file_path)
        config = config_file.add_mongodb_config(request)

        self.assertEqual(config.name, request.name)
        self.assertEqual(
            config.read_write_connection_string, request.read_write_connection_string
        )
        self.assertEqual(
            config.read_only_connection_string, request.read_only_connection_string
        )
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
            self.assertEqual(
                content,
                f'[{config.id}]\n'
                + 'type = mongodb_config\n'
                + 'name = bob@gmail.com\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
                + '\n',
            )

    def test_update_mongodb_config(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
            )
        config = ConfigFromFile(self.temp_file_path)

        request = UpdateMongoDbConfigRequest(
            id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
            new_name="bob@gmail.com",
            new_read_write_connection_string="mongodb://localhost:27020",
            new_read_only_connection_string="mongodb://localhost:27021",
        )
        config.update_mongodb_config(request)

        with open(self.temp_file_path, 'r') as f:
            content = f.read()
            self.assertEqual(
                content,
                "[5f50c31e8a7d4b1c9c9b0b1a]\n"
                + "type = mongodb_config\n"
                + "name = bob@gmail.com\n"
                + "read_write_connection_string = mongodb://localhost:27020\n"
                + "read_only_connection_string = mongodb://localhost:27021\n"
                + "\n",
            )

    def test_update_mongodb_client_unknown_id(self):
        config = ConfigFromFile(self.temp_file_path)
        request = UpdateMongoDbConfigRequest(
            id=ObjectId("5f50c31e8a7d4b1c9c9b0b1a"),
            new_name="bob@gmail.com",
            new_read_write_connection_string="mongodb://localhost:27020",
            new_read_only_connection_string="mongodb://localhost:27021",
        )

        with self.assertRaisesRegex(ValueError, "Cannot find MongoDB config .*"):
            config.update_mongodb_config(request)

    def test_update_mongodb_client_invalid_id(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1b]\n'
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
            )

        config = ConfigFromFile(self.temp_file_path)
        request = UpdateMongoDbConfigRequest(
            id=ObjectId("5f50c31e8a7d4b1c9c9b0b1b"),
            new_name="bob@gmail.com",
            new_read_write_connection_string="mongodb://localhost:27020",
            new_read_only_connection_string="mongodb://localhost:27021",
        )

        with self.assertRaisesRegex(ValueError, "ID .* is not a MongoDB config"):
            config.update_mongodb_config(request)

    def test_get_gphotos_configs(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
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
                + 'client_id = 5f50c31e8a7d4b1c9c9b0b1b\n'
                + 'object_id = 5f50c31e8a7d4b1c9c9b0b1d\n'
            )

        config_file = ConfigFromFile(self.temp_file_path)
        configs = config_file.get_gphotos_configs()

        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].id, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))
        self.assertEqual(configs[0].name, "TestGPhotos")
        self.assertEqual(configs[0].read_write_credentials.token, "test_token")
        self.assertEqual(
            configs[0].read_write_credentials.refresh_token, "test_refresh_token"
        )
        self.assertEqual(configs[0].read_write_credentials.client_id, "test_client_id")
        self.assertEqual(
            configs[0].read_write_credentials.client_secret, "test_client_secret"
        )
        self.assertEqual(
            configs[0].read_write_credentials.token_uri,
            "https://oauth2.googleapis.com/token",
        )
        self.assertEqual(configs[0].read_only_credentials.token, "test_token_2")
        self.assertEqual(
            configs[0].read_only_credentials.refresh_token, "test_refresh_token_2"
        )
        self.assertEqual(configs[0].read_only_credentials.client_id, "test_client_id_2")
        self.assertEqual(
            configs[0].read_only_credentials.client_secret, "test_client_secret_2"
        )
        self.assertEqual(
            configs[0].read_only_credentials.token_uri,
            "https://oauth2.googleapis.com/token",
        )

    def test_add_gphotos_config(self):
        request = AddGPhotosConfigRequest(
            name='bob@gmail.com',
            read_write_credentials=Credentials(
                token="token1",
                refresh_token="refresh_token_1",
                token_uri="https://oauth2.googleapis.com/token",
                client_id="client_id_1",
                client_secret="client_secret_1",
            ),
            read_only_credentials=Credentials(
                token="token2",
                refresh_token="refresh_token_2",
                token_uri="https://oauth2.googleapis.com/token",
                client_id="client_id_2",
                client_secret="client_secret_2",
            ),
        )
        config_file = ConfigFromFile(self.temp_file_path)
        config = config_file.add_gphotos_config(request)

        self.assertEqual(config.name, request.name)
        self.assert_credentials_are_equal(
            config.read_write_credentials, request.read_write_credentials
        )
        self.assert_credentials_are_equal(
            config.read_only_credentials, request.read_only_credentials
        )
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
            self.assertEqual(
                content,
                f"[{config.id}]\n"
                + "type = gphotos_config\n"
                + "name = bob@gmail.com\n"
                + "read_write_token = token1\n"
                + "read_write_refresh_token = refresh_token_1\n"
                + "read_write_client_id = client_id_1\n"
                + "read_write_client_secret = client_secret_1\n"
                + "read_write_token_uri = https://oauth2.googleapis.com/token\n"
                + "read_only_token = token2\n"
                + "read_only_refresh_token = refresh_token_2\n"
                + "read_only_client_id = client_id_2\n"
                + "read_only_client_secret = client_secret_2\n"
                + "read_only_token_uri = https://oauth2.googleapis.com/token\n"
                + "\n",
            )

    def test_update_gphotos_config(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1b]\n'
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
            )
        config_file = ConfigFromFile(self.temp_file_path)

        request = UpdateGPhotosConfigRequest(
            id=ObjectId('5f50c31e8a7d4b1c9c9b0b1b'),
            new_name='bob@gmail.com',
            new_read_write_credentials=Credentials(
                token="123",
                refresh_token="456",
                token_uri="https://yahoo.googleapis.com/token",
                client_id="myId",
                client_secret="mySecret",
            ),
            new_read_only_credentials=Credentials(
                token="abc",
                refresh_token="def",
                token_uri="https://yahoo.googleapis.com/token",
                client_id="myId",
                client_secret="mySecret",
            ),
        )
        config_file.update_gphotos_config(request)

        with open(self.temp_file_path, 'r') as f:
            content = f.read()
            self.assertEqual(
                content,
                '[5f50c31e8a7d4b1c9c9b0b1b]\n'
                + 'type = gphotos_config\n'
                + 'name = bob@gmail.com\n'
                + 'read_write_token = 123\n'
                + 'read_write_refresh_token = 456\n'
                + 'read_write_client_id = myId\n'
                + 'read_write_client_secret = mySecret\n'
                + 'read_write_token_uri = https://yahoo.googleapis.com/token\n'
                + 'read_only_token = abc\n'
                + 'read_only_refresh_token = def\n'
                + 'read_only_client_id = myId\n'
                + 'read_only_client_secret = mySecret\n'
                + 'read_only_token_uri = https://yahoo.googleapis.com/token\n'
                + "\n",
            )

    def test_update_gphotos_config_unknown_id(self):
        config_file = ConfigFromFile(self.temp_file_path)

        request = UpdateGPhotosConfigRequest(
            id=ObjectId('5f50c31e8a7d4b1c9c9b0b1b'),
            new_name='bob@gmail.com',
            new_read_write_credentials=Credentials(
                token="123",
                refresh_token="456",
                token_uri="https://yahoo.googleapis.com/token",
                client_id="myId",
                client_secret="mySecret",
            ),
            new_read_only_credentials=Credentials(
                token="abc",
                refresh_token="def",
                token_uri="https://yahoo.googleapis.com/token",
                client_id="myId",
                client_secret="mySecret",
            ),
        )

        with self.assertRaisesRegex(ValueError, "Cannot find GPhotos config .*"):
            config_file.update_gphotos_config(request)

    def test_update_gphotos_config_invalid_id(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
            )
        config_file = ConfigFromFile(self.temp_file_path)

        request = UpdateGPhotosConfigRequest(
            id=ObjectId('5f50c31e8a7d4b1c9c9b0b1a'),
            new_name='bob@gmail.com',
            new_read_write_credentials=Credentials(
                token="123",
                refresh_token="456",
                token_uri="https://yahoo.googleapis.com/token",
                client_id="myId",
                client_secret="mySecret",
            ),
            new_read_only_credentials=Credentials(
                token="abc",
                refresh_token="def",
                token_uri="https://yahoo.googleapis.com/token",
                client_id="myId",
                client_secret="mySecret",
            ),
        )

        with self.assertRaisesRegex(ValueError, "ID .* is not a GPhotos config"):
            config_file.update_gphotos_config(request)

    def test_get_root_album_id(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
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
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
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
            )

        config = ConfigFromFile(self.temp_file_path)
        with self.assertRaisesRegex(ValueError, "Cannot find root album"):
            config.get_root_album_id()

    def test_set_root_album_id(self):
        with open(self.temp_file_path, 'w') as f:
            f.write(
                '[5f50c31e8a7d4b1c9c9b0b1a]\n'
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
                + '\n'
                + '[5f50c31e8a7d4b1c9c9b0b1b]\n'
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

    def assert_credentials_are_equal(self, creds1: Credentials, creds2: Credentials):
        self.assertEqual(creds1.token, creds2.token)
        self.assertEqual(creds1.refresh_token, creds2.refresh_token)
        self.assertEqual(creds1.token_uri, creds2.token_uri)
        self.assertEqual(creds1.client_id, creds2.client_id)
        self.assertEqual(creds1.client_secret, creds2.client_secret)
