import unittest
from unittest.mock import patch
import mongomock
from pymongo import MongoClient

from sharded_photos_drive_cli_client.cli2.utils.config import build_config_from_options
from sharded_photos_drive_cli_client.shared.config.config_from_file import (
    ConfigFromFile,
)
from sharded_photos_drive_cli_client.shared.config.config_from_mongodb import (
    ConfigFromMongoDb,
)


class TestBuildConfigFromOptions(unittest.TestCase):

    def tearDown(self):
        patch.stopall()

    @patch.object(ConfigFromFile, '__init__', return_value=None)
    def test_build_config_from_file(self, mock_config_from_file):
        result = build_config_from_options(
            config_file="test_config.yaml", config_mongodb=None
        )

        self.assertIsNotNone(result)
        mock_config_from_file.assert_called_once_with("test_config.yaml")

    @patch('pymongo.MongoClient', return_value=mongomock.MongoClient())
    @patch.object(ConfigFromMongoDb, '__init__', return_value=None)
    def test_build_config_from_mongodb(
        self, mock_config_from_mongodb, mock_mongo_client
    ):
        result = build_config_from_options(
            config_file=None, config_mongodb="mongodb://localhost:27017"
        )

        self.assertIsNotNone(result)
        mock_config_from_mongodb.assert_called_once()
        mock_mongo_client.assert_called_once_with("mongodb://localhost:27017")

    def test_build_config_no_options(self):
        with self.assertRaises(ValueError):
            build_config_from_options(config_file=None, config_mongodb=None)

    @patch.object(ConfigFromFile, '__init__', return_value=None)
    def test_build_config_both_options(self, mock_config_from_file):
        result = build_config_from_options(
            config_file="test_config.yaml",
            config_mongodb="mongodb://localhost:27017",
        )

        self.assertIsNotNone(result)
        mock_config_from_file.assert_called_once_with("test_config.yaml")
