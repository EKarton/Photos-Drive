import json
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
                read_write_credentials=Credentials(
                    token="token1",
                    refresh_token="refreshToken1",
                    token_uri="google.com",
                    client_id="clientId1",
                    client_secret="clientSecret1",
                ),
                read_only_credentials=Credentials(
                    token="token2",
                    refresh_token="refreshToken2",
                    token_uri="google.com",
                    client_id="clientId2",
                    client_secret="clientSecret2",
                ),
            )
        )
        self.config.add_gphotos_config(
            AddGPhotosConfigRequest(
                name="sam@gmail.com",
                read_write_credentials=Credentials(
                    token="token3",
                    refresh_token="refreshToken3",
                    token_uri="google.com",
                    client_id="clientId3",
                    client_secret="clientSecret3",
                ),
                read_only_credentials=Credentials(
                    token="token4",
                    refresh_token="refreshToken4",
                    token_uri="google.com",
                    client_id="clientId4",
                    client_secret="clientSecret4",
                ),
            )
        )

    def test_build_from_config(self):
        repo = GPhotosClientsRepository.build_from_config(self.config)

        self.assertEqual(len(repo.get_all_clients()), 2)

    def test_build_from_config_with_token_refresh(self):
        repo = GPhotosClientsRepository.build_from_config(self.config)
        client = repo.get_client_by_id(self.config.get_gphotos_configs()[0].id)

        mock_refresh_response = Mock()
        mock_refresh_response.status = 200
        mock_refresh_response.headers = {}
        mock_refresh_response.data = json.dumps(
            {
                'access_token': "newToken123",
                'refresh_token': "newRefreshToken123",
            }
        ).encode('utf-8')

        mock_request = Mock()
        mock_request.return_value = mock_refresh_response
        client.session().credentials.refresh(mock_request)

        new_config = self.config.get_gphotos_configs()[0]
        self.assertEqual(new_config.read_write_credentials.token, 'newToken123')
        self.assertEqual(
            new_config.read_write_credentials.refresh_token, 'newRefreshToken123'
        )
        self.assertEqual(new_config.read_write_credentials.token_uri, 'google.com')
        self.assertEqual(new_config.read_write_credentials.client_id, 'clientId1')
        self.assertEqual(
            new_config.read_write_credentials.client_secret, 'clientSecret1'
        )

    def test_add_gphotos_client(self):
        client_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1c")
        client = Mock(spec=GPhotosClientV2)

        repo = GPhotosClientsRepository()
        repo.add_gphotos_client(client_id, client)

        self.assertEqual(repo.get_client_by_id(client_id), client)

    def test_add_gphotos_client_with_add_duplicate_gphotos_client(self):
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

    def test_get_client_by_id_with_id_not_found(self):
        repo = GPhotosClientsRepository()
        non_existent_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1f")

        with self.assertRaisesRegex(ValueError, "Cannot find Google Photos client .*"):
            repo.get_client_by_id(non_existent_id)

    def test_get_all_clients(self):
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

    def test_get_all_clients_with_empty_repo(self):
        repo = GPhotosClientsRepository()

        self.assertEqual(len(repo.get_all_clients()), 0)
