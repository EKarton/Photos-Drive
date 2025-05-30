import os
import tempfile
import unittest
from unittest.mock import patch
from unittest import mock
from typer.testing import CliRunner

from sharded_photos_drive_cli_client.cli2.app import build_app


class TestDbDump(unittest.TestCase):
    def setUp(self):
        self.tempDir = tempfile.TemporaryDirectory()

        self.mock_shutil_copy = patch("shutil.copy").start()
        self.mock_subproc_run = patch("subprocess.run").start()

    def tearDown(self):
        patch.stopall()
        self.tempDir.cleanup()

    def test_db_dump_with_config_file(self):
        config_file_path = os.path.join(self.tempDir.name, "dummy_config.yaml")
        with open(config_file_path, "w") as f:
            f.write(
                '[111111111111111111111111]\n'
                + 'type = mongodb_config\n'
                + 'name = TestMongoDB\n'
                + 'read_write_connection_string = mongodb://localhost:27017\n'
                + 'read_only_connection_string = mongodb://localhost:27016\n'
                + '\n'
                + '[222222222222222222222222]\n'
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
                + '[333333333333333333333333]\n'
                + 'type = root_album\n'
                + 'client_id = 111111111111111111111111\n'
                + 'object_id = 5f50c31e8a7d4b1c9c9b342\n'
            )

        # Mock config and its MongoDB configs
        mock_config = mock.Mock()
        mock_mongo = mock.Mock()
        mock_mongo.id = "11111111111111111111111"
        mock_mongo.read_write_connection_string = "mongodb://localhost:27017"
        mock_config.get_mongodb_configs.return_value = [mock_mongo]

        runner = CliRunner()
        result = runner.invoke(
            build_app(),
            ["db", "dump", self.tempDir.name, "--config-file", config_file_path],
        )

        self.assertIsNone(result.exception)
        self.assertEqual(result.exit_code, 0)
        self.mock_shutil_copy.assert_called_once_with(
            config_file_path, self.tempDir.name
        )
        self.mock_subproc_run.assert_called_with(
            [
                "mongodump",
                "--uri",
                "mongodb://localhost:27017",
                "--db",
                "sharded_google_photos",
                "--out",
                os.path.join(self.tempDir.name, "mongodb_111111111111111111111111"),
            ],
            check=True,
        )
