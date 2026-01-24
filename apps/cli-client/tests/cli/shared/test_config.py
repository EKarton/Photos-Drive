import unittest
from unittest.mock import patch

import mongomock
from pymongo import MongoClient

from photos_drive.cli.shared.config import build_config_from_options
from photos_drive.shared.core.config.config_from_file import (
    ConfigFromFile,
)
from photos_drive.shared.core.config.config_from_mongodb import (
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

    @patch.object(MongoClient, '__init__', return_value=None)
    @patch.object(MongoClient, '__new__', return_value=mongomock.MongoClient())
    @patch.object(ConfigFromMongoDb, '__init__', return_value=None)
    def test_build_config_from_mongodb(
        self, mock_config_from_mongodb, mock_mongo_client, _
    ):
        result = build_config_from_options(
            config_file=None, config_mongodb="mongodb://localhost:27017"
        )

        self.assertIsNotNone(result)
        mock_config_from_mongodb.assert_called_once()
        mock_mongo_client.assert_called_once_with(
            MongoClient, "mongodb://localhost:27017"
        )

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
