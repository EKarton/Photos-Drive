from typer.testing import CliRunner
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pymongo import MongoClient
from bson import ObjectId
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from sharded_photos_drive_cli_client.cli2.shared.inputs import (
    READ_ONLY_SCOPES,
    READ_WRITE_SCOPES,
)
from sharded_photos_drive_cli_client.cli2.app import build_app
from sharded_photos_drive_cli_client.shared.mongodb.albums import AlbumId
from sharded_photos_drive_cli_client.shared.mongodb.testing.mock_mongo_client import (
    create_mock_mongo_client,
)


class TestReauthorizeCli(unittest.TestCase):
    def setUp(self):
        self.mongodb_client_id = ObjectId()
        self.gphotos_client_id = ObjectId()
        self.root_album_id = AlbumId(self.mongodb_client_id, ObjectId())

        # Test setup 5: build fake config file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        with open(self.temp_file_path, 'w') as f:
            f.write(
                f'[{self.mongodb_client_id}]\n'
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
                + '\n'
                + f'[{self.gphotos_client_id}]\n'
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
                + f'client_id = {self.root_album_id.client_id}\n'
                + f'object_id = {self.root_album_id.object_id}\n'
            )

    def tearDown(self):
        patch.stopall()
        os.unlink(self.temp_file_path)

    def test_reauthorize_gphotos(self):
        # Test setup: mock getpass
        mock_get_pass = patch('getpass.getpass').start()
        mock_get_pass.side_effect = [
            'clientId1',
            'clientSecret1',
            'clientId2',
            'clientSecret2',
        ]

        # Test setup: mock InstalledAppFlow
        mock_iaf_1 = MagicMock()
        mock_iaf_1.credentials = Credentials(
            token="123",
            refresh_token="456",
            token_uri="google.com",
            client_id="clientId1",
            client_secret="clientSecret1",
            scopes=READ_WRITE_SCOPES,
        )
        mock_iaf_2 = MagicMock()
        mock_iaf_2.credentials = Credentials(
            token="abc",
            refresh_token="def",
            token_uri="python.com",
            client_id="clientId2",
            client_secret="clientSecret2",
            scopes=READ_ONLY_SCOPES,
        )
        mock_from_client_config = patch.object(
            InstalledAppFlow, 'from_client_config'
        ).start()
        mock_from_client_config.side_effect = [mock_iaf_1, mock_iaf_2]

        # Act: run the cli
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "config",
                "reauthorize",
                "gphotos",
                str(self.gphotos_client_id),
                "--config-file",
                self.temp_file_path,
            ],
            input="yes\nbob@gmail.com\nyes\nyes\n",
        )

        # Test assert: check on output
        self.assertEqual(
            result.output,
            'The account name is TestGPhotos\n'
            + 'Do you want to change the name? (Y/N): '
            + 'Enter new name: '
            + 'Do you want to change the read+write credentials? (Y/N): '
            + 'Do you want to change the read-only credentials? (Y/N): '
            + f'Successfully updated gphotos config {self.gphotos_client_id}\n',
        )
        self.assertEqual(result.exit_code, 0)

        # Test assert: check on config file
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
            self.assertIn('type = gphotos_config', content)
            self.assertIn('name = bob@gmail.com', content)
            self.assertIn('read_write_token = 123', content)
            self.assertIn('read_write_refresh_token = 456', content)
            self.assertIn('read_write_client_id = clientId1', content)
            self.assertIn('read_write_client_secret = clientSecret1', content)
            self.assertIn('read_write_token_uri = google.com', content)
            self.assertIn('read_only_token = abc', content)
            self.assertIn('read_only_refresh_token = def', content)
            self.assertIn('read_only_client_id = clientId2', content)
            self.assertIn('read_only_client_secret = clientSecret2', content)
            self.assertIn('read_only_token_uri = python.com', content)

    def test_reauthorize_mongodb(self):
        # Test setup: mock MongoClient
        mongodb_client = create_mock_mongo_client()
        patch.object(MongoClient, '__init__', return_value=None).start()
        patch.object(MongoClient, '__new__', return_value=mongodb_client).start()

        # Test setup: mock getpass
        mock_get_pass = patch('getpass.getpass').start()
        mock_get_pass.side_effect = [
            'mongodb://localhost:8080',
            'mongodb://localhost:9090',
        ]

        # Act: run the cli
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "config",
                "reauthorize",
                "mongodb",
                str(self.mongodb_client_id),
                "--config-file",
                self.temp_file_path,
            ],
            input="yes\nbob@gmail.com\nyes\nyes\n",
        )

        # Test assert: check on output
        self.assertEqual(
            result.output,
            'The account name is TestMongoDB\n'
            + 'Do you want to change the name? (Y/N): '
            + 'Enter new name: '
            + 'Do you want to change the read+write connection string? (Y/N): '
            + 'Do you want to change the read+only connection string? (Y/N): '
            + f'Successfully updated mongodb config {self.mongodb_client_id}\n',
        )
        self.assertEqual(result.exit_code, 0)

        # Test assert: check on config file
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
            self.assertIn('type = mongodb_config', content)
            self.assertIn('name = bob@gmail.com', content)
            self.assertIn(
                'read_write_connection_string = mongodb://localhost:8080', content
            )
            self.assertIn(
                'read_only_connection_string = mongodb://localhost:9090', content
            )
