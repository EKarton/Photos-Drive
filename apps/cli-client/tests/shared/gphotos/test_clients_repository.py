import unittest
from unittest.mock import Mock
from bson.objectid import ObjectId

from sharded_photos_drive_cli_client.shared.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from sharded_photos_drive_cli_client.shared.gphotos.client import GPhotosClientV2
from sharded_photos_drive_cli_client.shared.config.config import Config


class TestGPhotosClientsRepository(unittest.TestCase):
    def setUp(self):
        self.repo = GPhotosClientsRepository()
        self.mock_config = Mock(spec=Config)
        self.mock_config.get_gphotos_clients.return_value = [
            (ObjectId("5f50c31e8a7d4b1c9c9b0b1a"), Mock(spec=GPhotosClientV2)),
            (ObjectId("5f50c31e8a7d4b1c9c9b0b1b"), Mock(spec=GPhotosClientV2)),
        ]

    def test_build_from_config_repo__adds_gphotos_clients_from_config(self):
        repo = GPhotosClientsRepository.build_from_config_repo(self.mock_config)

        self.assertEqual(len(repo.get_all_clients()), 2)

    def test_add_gphotos_client__adds_gphotos_client_to_repo(self):
        client_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1c")
        client = Mock(spec=GPhotosClientV2)

        self.repo.add_gphotos_client(client_id, client)

        self.assertEqual(self.repo.get_client_by_id(client_id), client)

    def test_add_gphotos_client__add_duplicate_gphotos_client__throws_error(self):
        client_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1d")
        client = Mock(spec=GPhotosClientV2)

        self.repo.add_gphotos_client(client_id, client)

        with self.assertRaisesRegex(
            ValueError, f"GPhotos Client ID {client_id} already exists"
        ):
            self.repo.add_gphotos_client(client_id, client)

    def test_get_client_by_id(self):
        client_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1e")
        client = Mock(spec=GPhotosClientV2)

        self.repo.add_gphotos_client(client_id, client)

        self.assertEqual(self.repo.get_client_by_id(client_id), client)

    def test_get_client_by_id_not_found(self):
        non_existent_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1f")

        with self.assertRaisesRegex(
            ValueError, f"Cannot find Google Photos client with ID {non_existent_id}"
        ):
            self.repo.get_client_by_id(non_existent_id)

    def test_get_all_clients__returns_all_gphotos_clients(self):
        client_id1 = ObjectId("5f50c31e8a7d4b1c9c9b0b20")
        client_id2 = ObjectId("5f50c31e8a7d4b1c9c9b0b21")
        client1 = Mock(spec=GPhotosClientV2)
        client2 = Mock(spec=GPhotosClientV2)
        self.repo.add_gphotos_client(client_id1, client1)
        self.repo.add_gphotos_client(client_id2, client2)

        all_clients = self.repo.get_all_clients()

        self.assertEqual(len(all_clients), 2)
        self.assertIn((client_id1, client1), all_clients)
        self.assertIn((client_id2, client2), all_clients)

    def test_get_all_clients_empty_repo(self):
        self.assertEqual(len(self.repo.get_all_clients()), 0)
