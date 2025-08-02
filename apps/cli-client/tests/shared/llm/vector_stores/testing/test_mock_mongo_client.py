import unittest
from bson.objectid import ObjectId
from pymongo.errors import CollectionInvalid

from photos_drive.shared.llm.vector_stores.testing.mock_mongo_client import (
    MockCollection,
    MockDatabase,
    MockMongoClient,
)


class TestMockCollection(unittest.TestCase):
    def setUp(self):
        self.collection = MockCollection("test_collection", MockDatabase())

    def test_insert_many_and_find_one(self):
        docs = [{"foo": 1}, {"foo": 2}]
        result = self.collection.insert_many(docs)
        self.assertEqual(len(result.inserted_ids), 2)

        # Check each inserted doc has an _id and is stored
        for _id in result.inserted_ids:
            stored_doc = self.collection.find_one({"_id": _id})
            self.assertIsNotNone(stored_doc)
            self.assertIn("_id", stored_doc)

        # find_one on non-existing _id returns None
        self.assertIsNone(self.collection.find_one({"_id": ObjectId()}))

    def test_delete_many_deletes_and_returns_count(self):
        docs = [{"foo": i} for i in range(5)]
        inserted = self.collection.insert_many(docs)

        # Delete two documents
        delete_ids = inserted.inserted_ids[:2]
        result = self.collection.delete_many({"_id": {"$in": delete_ids}})
        self.assertEqual(result.deleted_count, 2)

        # Confirm they are deleted
        for _id in delete_ids:
            self.assertIsNone(self.collection.find_one({"_id": _id}))

        # Delete documents that don’t exist results in count 0
        new_id = ObjectId()
        result = self.collection.delete_many({"_id": {"$in": [new_id]}})
        self.assertEqual(result.deleted_count, 0)

    def test_aggregate_returns_documents_with_limit(self):
        # Insert 5 documents
        docs = [{"foo": i} for i in range(5)]
        self.collection.insert_many(docs)

        # Pipeline with $vectorSearch with limit=3
        results = list(self.collection.aggregate([{"$vectorSearch": {"limit": 3}}]))
        self.assertEqual(len(results), 3)

        # Pipeline without $vectorSearch returns all docs
        results = list(self.collection.aggregate([{"$match": {"foo": {"$gte": 0}}}]))
        self.assertEqual(len(results), 5)

    def test_list_search_indexes_and_create_search_index_are_callable(self):
        # Confirm these methods are callable and return None
        self.assertEqual(self.collection.list_search_indexes(), [])
        self.assertIsNone(self.collection.create_search_index())

    def test_insert_many_assigns_unique_ids(self):
        docs = [{"foo": "a"}, {"foo": "b"}, {"foo": "c"}]
        result = self.collection.insert_many(docs)
        inserted_ids_set = set(result.inserted_ids)
        self.assertEqual(len(inserted_ids_set), 3)  # Unique IDs assigned


class TestMockDatabase(unittest.TestCase):
    def setUp(self):
        self.db = MockDatabase()

    def test_getitem_returns_collection_and_creates_if_missing(self):
        col1 = self.db["col1"]
        col2 = self.db["col2"]
        self.assertIsInstance(col1, MockCollection)
        self.assertIsInstance(col2, MockCollection)
        self.assertEqual(col1.name, "col1")
        self.assertEqual(col2.name, "col2")

        # Accessing again returns same collection object
        col1_again = self.db["col1"]
        self.assertIs(col1, col1_again)

    def test_command_dbStats_default_and_custom(self):
        # Default dbStats returns dummy data
        stats = self.db.command({"dbStats": 1})
        self.assertIn("totalFreeStorageSize", stats)
        self.assertIn("storageSize", stats)
        self.assertIn("objects", stats)

        # Set custom db stats and verify
        custom_stats = {
            "totalFreeStorageSize": 12345,
            "storageSize": 54321,
            "objects": 9,
        }
        self.db.set_db_stats(custom_stats)
        stats2 = self.db.command({"dbStats": 1})
        self.assertEqual(stats2, custom_stats)

    def test_command_raises_not_implemented_for_unknown_command(self):
        with self.assertRaises(NotImplementedError):
            self.db.command({"invalidCommand": 1})

    def test_create_collection_new_and_existing(self):
        db = MockDatabase()
        col_name = "new_collection"
        db.create_collection(col_name)
        self.assertIn(col_name, db.collections)
        self.assertIsInstance(db.collections[col_name], MockCollection)
        self.assertEqual(db.collections[col_name].name, col_name)

    def test_create_collection_on_existing_collection(self):
        db = MockDatabase()
        col_name = "new_collection"
        db.create_collection(col_name)

        with self.assertRaises(CollectionInvalid):
            db.create_collection(col_name)


class TestMockMongoClient(unittest.TestCase):
    def setUp(self):
        self.client = MockMongoClient()

    def test_getitem_returns_database_and_creates_if_missing(self):
        db1 = self.client["db1"]
        db2 = self.client["db2"]
        self.assertIsInstance(db1, MockDatabase)
        self.assertIsInstance(db2, MockDatabase)

        # Accessing again returns same database object
        db1_again = self.client["db1"]
        self.assertIs(db1, db1_again)

    def test_start_session_returns_dummy_session_context_manager(self):
        session = self.client.start_session()
        self.assertTrue(hasattr(session, "__enter__"))
        self.assertTrue(hasattr(session, "__exit__"))

        with session:
            # inside the context, session should be the DummySession instance
            self.assertIs(session, session)

        # Call dummy transaction methods and ensure no exception
        session.start_transaction()
        session.commit_transaction()
        session.abort_transaction()
        session.end_session()

        # The boolean value of DummySession should be False
        self.assertFalse(bool(session))
