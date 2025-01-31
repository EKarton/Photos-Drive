import unittest
from unittest.mock import Mock
from bson.objectid import ObjectId
from google.oauth2.credentials import Credentials

from sharded_photos_drive_cli_client.shared.config.inmemory_config import InMemoryConfig
from sharded_photos_drive_cli_client.shared.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from sharded_photos_drive_cli_client.shared.gphotos.client import GPhotosClientV2
from sharded_photos_drive_cli_client.shared.config.config import (
    AddGPhotosConfigRequest,
)


class TestGPhotosClientsRepository(unittest.TestCase):
    def setUp(self):
        self.config = InMemoryConfig()
        self.config.add_gphotos_config(
            AddGPhotosConfigRequest(
                name="bob@gmail.com",
                read_write_credentials=Mock(spec=Credentials),
                read_only_credentials=Mock(specs=Credentials),
            )
        )
        self.config.add_gphotos_config(
            AddGPhotosConfigRequest(
                name="sam@gmail.com",
                read_write_credentials=Mock(spec=Credentials),
                read_only_credentials=Mock(specs=Credentials),
            )
        )

    def test_build_from_config_repo__adds_gphotos_clients_from_config(self):
        repo = GPhotosClientsRepository.build_from_config(self.config)

        self.assertEqual(len(repo.get_all_clients()), 2)

    def test_add_gphotos_client__adds_gphotos_client_to_repo(self):
        client_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1c")
        client = Mock(spec=GPhotosClientV2)

        repo = GPhotosClientsRepository()
        repo.add_gphotos_client(client_id, client)

        self.assertEqual(repo.get_client_by_id(client_id), client)

    def test_add_gphotos_client__add_duplicate_gphotos_client__throws_error(self):
        client_id = self.config.get_gphotos_configs()[0].id
        repo = GPhotosClientsRepository.build_from_config(self.config)

        with self.assertRaisesRegex(
            ValueError, f"GPhotos Client ID {client_id} already exists"
        ):
            client = Mock(spec=GPhotosClientV2)
            repo.add_gphotos_client(client_id, client)

    def test_get_client_by_id(self):
        client_config = self.config.get_gphotos_configs()[0]

        repo = GPhotosClientsRepository.build_from_config(self.config)
        client = repo.get_client_by_id(client_config.id)

        self.assertIsInstance(client, GPhotosClientV2)
        self.assertEqual(client.name(), client_config.name)

    def test_get_client_by_id_not_found(self):
        repo = GPhotosClientsRepository()
        non_existent_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1f")

        with self.assertRaisesRegex(ValueError, "Cannot find Google Photos client .*"):
            repo.get_client_by_id(non_existent_id)

    def test_get_all_clients__returns_all_gphotos_clients(self):
        repo = GPhotosClientsRepository()
        client_id1 = ObjectId("5f50c31e8a7d4b1c9c9b0b20")
        client_id2 = ObjectId("5f50c31e8a7d4b1c9c9b0b21")
        client1 = Mock(spec=GPhotosClientV2)
        client2 = Mock(spec=GPhotosClientV2)
        repo.add_gphotos_client(client_id1, client1)
        repo.add_gphotos_client(client_id2, client2)

        all_clients = repo.get_all_clients()

        self.assertEqual(len(all_clients), 2)
        self.assertIn((client_id1, client1), all_clients)
        self.assertIn((client_id2, client2), all_clients)

    def test_get_all_clients_empty_repo(self):
        repo = GPhotosClientsRepository()

        self.assertEqual(len(repo.get_all_clients()), 0)
