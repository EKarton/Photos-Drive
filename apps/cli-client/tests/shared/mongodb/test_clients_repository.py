import unittest
from unittest.mock import Mock
from bson.objectid import ObjectId
import mongomock

from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
)
from sharded_photos_drive_cli_client.shared.config.config import Config


class TestMongoDbClientsRepository(unittest.TestCase):
    def test_build_from_config__fetches_and_adds_mongodb_client_to_repo(self):
        mock_config = Mock(Config)
        client_1_id = ObjectId()
        client_2_id = ObjectId()
        client_1 = mongomock.MongoClient()
        client_2 = mongomock.MongoClient()
        mock_config.get_mongo_db_clients.return_value = [
            (client_1_id, client_1),
            (client_2_id, client_2),
        ]

        repo = MongoDbClientsRepository.build_from_config(mock_config)
        clients = repo.get_all_clients()

        self.assertEqual(len(clients), 2)
        self.assertEqual(clients[0][0], client_1_id)
        self.assertEqual(clients[0][1], client_1)
        self.assertEqual(clients[1][0], client_2_id)
        self.assertEqual(clients[1][1], client_2)

    def test_add_mongodb_client__adds_mongodb_client_to_repo(self):
        client_id = ObjectId()
        client = self.__create_mongodb_client__()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id, client)

        # Verify that the client was added successfully
        retrieved_client = repo.get_client_by_id(client_id)
        self.assertEqual(retrieved_client, client)

    def test_add_mongodb_client__duplicate_mongodb_clients_added__throws_error(self):
        client_id = ObjectId()
        client = self.__create_mongodb_client__()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id, client)

        with self.assertRaisesRegex(ValueError, "Mongo DB Client ID .* already exists"):
            client_2 = self.__create_mongodb_client__()
            repo.add_mongodb_client(client_id, client_2)

    def test_get_client_by_id__invalid_id__throws_error(self):
        non_existent_id = ObjectId()
        repo = MongoDbClientsRepository()

        with self.assertRaisesRegex(
            ValueError, "Cannot find MongoDB client with ID .*"
        ):
            repo.get_client_by_id(non_existent_id)

    def test_find_id_of_client_with_most_space__returns_client_id_with_most_amount_of_space(
        self,
    ):
        client_id_2 = ObjectId()
        client_id_1 = ObjectId()
        client_1 = self.__create_mongodb_client__(1000)
        client_2 = self.__create_mongodb_client__(2000)
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        best_client_id = repo.find_id_of_client_with_most_space()

        self.assertEqual(best_client_id, client_id_2)

    def test_find_id_of_client_with_most_space__with_no_mongodb_client__throws_error(
        self,
    ):
        repo = MongoDbClientsRepository()

        with self.assertRaisesRegex(ValueError, "No MongoDB Client!"):
            repo.find_id_of_client_with_most_space()

    def test_get_all_clients__returns_all_mongodb_clients(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = self.__create_mongodb_client__()
        client_2 = self.__create_mongodb_client__()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        all_clients = repo.get_all_clients()

        self.assertEqual(len(all_clients), 2)
        self.assertIn((client_id_1, client_1), all_clients)
        self.assertIn((client_id_2, client_2), all_clients)

    def __create_mongodb_client__(self, total_free_storage_size: int = 1000):
        mock_client = mongomock.MongoClient()
        mock_client["sharded_google_photos"].command = Mock(
            return_value={"totalFreeStorageSize": total_free_storage_size}
        )

        return mock_client
