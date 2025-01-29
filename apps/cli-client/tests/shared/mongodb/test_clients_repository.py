from typing import cast
import unittest
from unittest.mock import Mock
from bson.objectid import ObjectId

from sharded_photos_drive_cli_client.shared.config.inmemory_config import InMemoryConfig
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    BYTES_512MB,
    MongoDbClientsRepository,
    MongoDbTransactionsContext,
)
from sharded_photos_drive_cli_client.shared.config.config import (
    AddMongoDbConfigRequest,
)
from sharded_photos_drive_cli_client.shared.mongodb.testing import (
    create_mock_mongo_client,
)


class TestMongoDbClientsRepository(unittest.TestCase):
    def test_build_from_config__fetches_and_adds_mongodb_client_to_repo(self):
        mock_config = InMemoryConfig()
        mongodb_config_1 = mock_config.add_mongodb_config(
            AddMongoDbConfigRequest(
                name="bob@gmail.com",
                read_write_connection_string="localhost:5572",
                read_only_connection_string="localhost:5573",
            )
        )
        mongodb_config_2 = mock_config.add_mongodb_config(
            AddMongoDbConfigRequest(
                name="sam@gmail.com",
                read_write_connection_string="localhost:5574",
                read_only_connection_string="localhost:5575",
            )
        )

        repo = MongoDbClientsRepository.build_from_config(mock_config)
        clients = repo.get_all_clients()

        self.assertEqual(len(clients), 2)
        self.assertEqual(clients[0][0], mongodb_config_1.id)
        self.assertEqual(clients[1][0], mongodb_config_2.id)

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

        with self.assertRaisesRegex(ValueError, "Cannot find MongoDB client .*"):
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

        with self.assertRaisesRegex(
            ValueError, "No MongoDB client found with free space!"
        ):
            repo.find_id_of_client_with_most_space()

    def test_find_id_of_client_with_most_space__no_mongodb_client_with_free_space(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client(
            total_free_storage_size=0, storage_size=BYTES_512MB
        )
        client_2 = create_mock_mongo_client(
            total_free_storage_size=0, storage_size=BYTES_512MB
        )
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)
        with self.assertRaisesRegex(
            ValueError, "No MongoDB client found with free space!"
        ):
            repo.find_id_of_client_with_most_space()

    def test_find_id_of_client_with_most_space__no_total_free_storage_size(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client(
            total_free_storage_size=0, storage_size=1000
        )
        client_2 = create_mock_mongo_client(
            total_free_storage_size=0, storage_size=2000
        )
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        best_client_id = repo.find_id_of_client_with_most_space()

        self.assertEqual(best_client_id, client_id_1)

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

        client_1_session = cast(Mock, client_1.start_session).return_value
        client_2_session = cast(Mock, client_1.start_session).return_value
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

        client_1_session = cast(Mock, client_1.start_session).return_value
        client_2_session = cast(Mock, client_1.start_session).return_value
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

        client_1_session = cast(Mock, client_1.start_session).return_value
        client_2_session = cast(Mock, client_1.start_session).return_value
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

        client_1_session = cast(Mock, client_1.start_session).return_value
        client_2_session = cast(Mock, client_1.start_session).return_value
        self.assertTrue(client_1_session.abort_transaction.call_count == 1)
        self.assertTrue(client_2_session.abort_transaction.call_count == 1)
        self.assertTrue(client_1_session.end_session.call_count == 1)
        self.assertTrue(client_2_session.end_session.call_count == 1)
