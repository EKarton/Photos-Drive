import unittest
from unittest.mock import Mock
from bson.objectid import ObjectId

from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
    MongoDbTransactionsContext,
)
from sharded_photos_drive_cli_client.shared.config.config import Config
from sharded_photos_drive_cli_client.shared.mongodb.testing import (
    create_mock_mongo_client,
)


class TestMongoDbClientsRepository(unittest.TestCase):
    def test_build_from_config__fetches_and_adds_mongodb_client_to_repo(self):
        mock_config = Mock(Config)
        client_1_id = ObjectId()
        client_2_id = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
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
        client = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id, client)

        # Verify that the client was added successfully
        retrieved_client = repo.get_client_by_id(client_id)
        self.assertEqual(retrieved_client, client)

    def test_add_mongodb_client__duplicate_mongodb_clients_added__throws_error(self):
        client_id = ObjectId()
        client = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id, client)

        with self.assertRaisesRegex(ValueError, "Mongo DB Client ID .* already exists"):
            client_2 = create_mock_mongo_client()
            repo.add_mongodb_client(client_id, client_2)

    def test_add_mongodb_client__in_transaction__throws_error(self):
        client_id = ObjectId()
        client = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.start_transactions()

        with self.assertRaisesRegex(ValueError, "Transaction is still in progress"):
            repo.add_mongodb_client(client_id, client)

    def test_get_client_by_id__invalid_id__throws_error(self):
        non_existent_id = ObjectId()
        repo = MongoDbClientsRepository()

        with self.assertRaisesRegex(
            ValueError, "Cannot find MongoDB client with ID .*"
        ):
            repo.get_client_by_id(non_existent_id)

    def test_find_id_of_client_with_most_space(self):
        client_id_2 = ObjectId()
        client_id_1 = ObjectId()
        client_1 = create_mock_mongo_client(1000)
        client_2 = create_mock_mongo_client(2000)
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        best_client_id = repo.find_id_of_client_with_most_space()

        self.assertEqual(best_client_id, client_id_2)

    def test_find_id_of_client_with_most_space__with_no_mongodb_client(self):
        repo = MongoDbClientsRepository()

        with self.assertRaisesRegex(ValueError, "No MongoDB Client!"):
            repo.find_id_of_client_with_most_space()

    def test_get_all_clients__returns_all_mongodb_clients(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        all_clients = repo.get_all_clients()

        self.assertEqual(len(all_clients), 2)
        self.assertIn((client_id_1, client_1), all_clients)
        self.assertIn((client_id_2, client_2), all_clients)

    def test_start_transactions__creates_sessions(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        repo.start_transactions()

        self.assertIsInstance(repo.get_session_for_client_id(client_id_1), Mock)
        self.assertIsInstance(repo.get_session_for_client_id(client_id_2), Mock)

    def test_start_transactions__in_transaction__throws_error(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)
        repo.start_transactions()

        with self.assertRaisesRegex(ValueError, "Transaction already in progress"):
            repo.start_transactions()

    def test_commit_and_end_transactions(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)
        repo.start_transactions()

        repo.commit_and_end_transactions()

        client_1_session = client_1.start_session.return_value
        client_2_session = client_1.start_session.return_value
        self.assertTrue(client_1_session.commit_transaction.call_count == 1)
        self.assertTrue(client_2_session.commit_transaction.call_count == 1)
        self.assertTrue(client_1_session.end_session.call_count == 1)
        self.assertTrue(client_2_session.end_session.call_count == 1)

    def test_commit_and_end_transactions_ends_transactions_can_start_new_transaction(
        self,
    ):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)
        repo.start_transactions()

        repo.commit_and_end_transactions()
        repo.start_transactions()

    def test_commit_and_end_transactions__not_in_transaction(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        with self.assertRaisesRegex(ValueError, "Transaction not in progress"):
            repo.commit_and_end_transactions()

    def test_abort_and_end_transactions(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)
        repo.start_transactions()

        repo.abort_and_end_transactions()

        client_1_session = client_1.start_session.return_value
        client_2_session = client_1.start_session.return_value
        self.assertTrue(client_1_session.abort_transaction.call_count == 1)
        self.assertTrue(client_2_session.abort_transaction.call_count == 1)
        self.assertTrue(client_1_session.end_session.call_count == 1)
        self.assertTrue(client_2_session.end_session.call_count == 1)

    def test_abort_and_end_transactions__not_in_transaction(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        with self.assertRaisesRegex(ValueError, "Transaction not in progress"):
            repo.abort_and_end_transactions()


class TestMongoDbTransactionsContext(unittest.TestCase):
    def test_successful_operation__commits_transactions(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        with MongoDbTransactionsContext(repo):
            pass

        client_1_session = client_1.start_session.return_value
        client_2_session = client_1.start_session.return_value
        self.assertTrue(client_1_session.commit_transaction.call_count == 1)
        self.assertTrue(client_2_session.commit_transaction.call_count == 1)
        self.assertTrue(client_1_session.end_session.call_count == 1)
        self.assertTrue(client_2_session.end_session.call_count == 1)

    def test_error_thrown__aborts_transactions_and_raises_exception(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        with self.assertRaisesRegex(ValueError, "Random error"):
            with MongoDbTransactionsContext(repo):
                raise ValueError("Random error")

        client_1_session = client_1.start_session.return_value
        client_2_session = client_1.start_session.return_value
        self.assertTrue(client_1_session.abort_transaction.call_count == 1)
        self.assertTrue(client_2_session.abort_transaction.call_count == 1)
        self.assertTrue(client_1_session.end_session.call_count == 1)
        self.assertTrue(client_2_session.end_session.call_count == 1)
