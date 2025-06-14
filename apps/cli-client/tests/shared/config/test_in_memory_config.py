import unittest
from bson import ObjectId
from unittest.mock import MagicMock
from google.oauth2.credentials import Credentials

from photos_drive.shared.config.config import (
    AddGPhotosConfigRequest,
    AddMongoDbConfigRequest,
    UpdateGPhotosConfigRequest,
    UpdateMongoDbConfigRequest,
)
from photos_drive.shared.config.inmemory_config import InMemoryConfig
from photos_drive.shared.metadata.album_id import AlbumId


class TestInMemoryConfig(unittest.TestCase):
    def setUp(self):
        self.config = InMemoryConfig()

    def test_add_and_get_mongodb_config(self):
        request = AddMongoDbConfigRequest(
            name="Test MongoDB",
            read_write_connection_string="mongodb://localhost:27017",
            read_only_connection_string="mongodb://localhost:27017",
        )
        config = self.config.add_mongodb_config(request)

        configs = self.config.get_mongodb_configs()

        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].name, "Test MongoDB")
        self.assertEqual(configs[0].id, config.id)

    def test_update_mongodb_config(self):
        request = AddMongoDbConfigRequest(
            name="Test MongoDB",
            read_write_connection_string="mongodb://localhost:27017",
            read_only_connection_string="mongodb://localhost:27017",
        )
        config = self.config.add_mongodb_config(request)
        update_request = UpdateMongoDbConfigRequest(
            id=config.id,
            new_name="Updated MongoDB",
            new_read_write_connection_string="mongodb://localhost:27018",
            new_read_only_connection_string="mongodb://localhost:27018",
        )

        self.config.update_mongodb_config(update_request)

        updated_config = self.config.get_mongodb_configs()[0]
        self.assertEqual(updated_config.name, "Updated MongoDB")
        self.assertEqual(
            updated_config.read_write_connection_string, "mongodb://localhost:27018"
        )

    def test_update_mongodb_config_with_non_existant_id(self):
        update_request = UpdateMongoDbConfigRequest(
            id=ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
            new_name="Updated MongoDB",
            new_read_write_connection_string="mongodb://localhost:27018",
            new_read_only_connection_string="mongodb://localhost:27018",
        )

        with self.assertRaisesRegex(ValueError, "Mongo Config ID .* does not exist"):
            self.config.update_mongodb_config(update_request)

    def test_add_and_get_gphotos_config(self):
        mock_credentials = MagicMock(spec=Credentials)
        request = AddGPhotosConfigRequest(
            name="Test GPhotos",
            read_write_credentials=mock_credentials,
            read_only_credentials=mock_credentials,
        )
        config = self.config.add_gphotos_config(request)

        configs = self.config.get_gphotos_configs()

        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].name, "Test GPhotos")
        self.assertEqual(configs[0].id, config.id)

    def test_update_gphotos_config(self):
        mock_credentials = MagicMock(spec=Credentials)
        request = AddGPhotosConfigRequest(
            name="Test GPhotos",
            read_write_credentials=mock_credentials,
            read_only_credentials=mock_credentials,
        )
        config = self.config.add_gphotos_config(request)

        new_mock_credentials = MagicMock(spec=Credentials)
        update_request = UpdateGPhotosConfigRequest(
            id=config.id,
            new_name="Updated GPhotos",
            new_read_write_credentials=new_mock_credentials,
            new_read_only_credentials=new_mock_credentials,
        )
        self.config.update_gphotos_config(update_request)

        updated_config = self.config.get_gphotos_configs()[0]
        self.assertEqual(updated_config.name, "Updated GPhotos")
        self.assertEqual(updated_config.read_write_credentials, new_mock_credentials)

    def test_update_gphotos_config_with_non_existant_id(self):
        new_mock_credentials = MagicMock(spec=Credentials)
        update_request = UpdateGPhotosConfigRequest(
            id=ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
            new_name="Updated GPhotos",
            new_read_write_credentials=new_mock_credentials,
            new_read_only_credentials=new_mock_credentials,
        )

        with self.assertRaisesRegex(ValueError, "GPhotos Config ID .* does not exist"):
            self.config.update_gphotos_config(update_request)

    def test_set_and_get_root_album_id(self):
        album_id = AlbumId(
            client_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1e"),
            object_id=ObjectId("5f50c31e8a7d4b1c9c9b0b1f"),
        )

        self.config.set_root_album_id(album_id)
        retrieved_id = self.config.get_root_album_id()

        self.assertEqual(retrieved_id, album_id)

    def test_get_root_album_id_not_set(self):
        with self.assertRaises(ValueError):
            self.config.get_root_album_id()
