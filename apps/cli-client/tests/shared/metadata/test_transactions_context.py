from typing import cast
import unittest
from unittest.mock import Mock

from bson.objectid import ObjectId

from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.mongodb.testing import (
    create_mock_mongo_client,
)
from photos_drive.shared.metadata.transactions_context import (
    TransactionsContext,
)


class TestTransactionsContext(unittest.TestCase):
    def test_successful_operation__commits_transactions(self):
        client_id_1 = ObjectId()
        client_id_2 = ObjectId()
        client_1 = create_mock_mongo_client()
        client_2 = create_mock_mongo_client()
        repo = MongoDbClientsRepository()
        repo.add_mongodb_client(client_id_1, client_1)
        repo.add_mongodb_client(client_id_2, client_2)

        with TransactionsContext(repo):
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
            with TransactionsContext(repo):
                raise ValueError("Random error")

        client_1_session = cast(Mock, client_1.start_session).return_value
        client_2_session = cast(Mock, client_1.start_session).return_value
        self.assertTrue(client_1_session.abort_transaction.call_count == 1)
        self.assertTrue(client_2_session.abort_transaction.call_count == 1)
        self.assertTrue(client_1_session.end_session.call_count == 1)
        self.assertTrue(client_2_session.end_session.call_count == 1)
