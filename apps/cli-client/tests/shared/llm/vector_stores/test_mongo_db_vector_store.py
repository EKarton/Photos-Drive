from datetime import datetime, timezone
import unittest

from bson.binary import Binary
from bson.objectid import ObjectId
import numpy as np

from photos_drive.shared.llm.vector_stores.base_vector_store import (
    CreateMediaItemEmbeddingRequest,
    MediaItemEmbeddingId,
    QueryMediaItemEmbeddingRequest,
)
from photos_drive.shared.llm.vector_stores.mongo_db_vector_store import (
    MongoDbVectorStore,
)
from photos_drive.shared.llm.vector_stores.testing.mock_mongo_client import (
    MockMongoClient,
)
from photos_drive.shared.metadata.media_item_id import MediaItemId

MOCK_MEDIA_ITEM_ID_1 = MediaItemId(ObjectId(), ObjectId())
MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0, tzinfo=timezone.utc)


class TestMongoDbVectorStore(unittest.TestCase):
    def setUp(self):
        # Setup mock MongoDB client (your MockMongoClient with .database fixes)
        self.mock_client = MockMongoClient()

        # Create the vector store instance pointing to mock DB and collection
        self.store_id = ObjectId()
        self.embedding_dimensions = 16
        self.collection_name = "test_embeddings"

        self.store = MongoDbVectorStore(
            store_id=self.store_id,
            mongodb_client=self.mock_client,
            db_name="photos_drive",
            collection_name=self.collection_name,
            embedding_dimensions=self.embedding_dimensions,
        )

    def test_init_does_not_make_two_collections(self):
        MongoDbVectorStore(
            store_id=self.store_id,
            mongodb_client=self.mock_client,
            db_name="photos_drive",
            collection_name=self.collection_name,
            embedding_dimensions=self.embedding_dimensions,
        )

        self.assertEqual(len(self.mock_client['photos_drive'].collections), 1)

    def test_get_store_id(self):
        self.assertEqual(self.store.get_store_id(), self.store_id)

    def test_get_available_space_returns_positive(self):
        space = self.store.get_available_space()
        self.assertIsInstance(space, int)
        self.assertGreater(space, 0)

    def test_get_available_space_with_no_data_returns_positive(self):
        self.mock_client['photos_drive'].set_db_stats(
            {
                "totalFreeStorageSize": 0,
                "storageSize": 100_000,
                "objects": 0,
            }
        )
        space = self.store.get_available_space()
        self.assertEqual(space, 536770912)

    def test_add_documents_and_verify_stored(self):
        embedding = self._make_embedding(0.5)
        req = CreateMediaItemEmbeddingRequest(
            embedding=embedding,
            media_item_id=MOCK_MEDIA_ITEM_ID_1,
            date_taken=MOCK_DATE_TAKEN,
        )

        # Add document
        docs = self.store.add_media_item_embeddings([req])
        self.assertEqual(len(docs), 1)
        doc = docs[0]

        # Check Document returned
        self.assertEqual(doc.media_item_id, MOCK_MEDIA_ITEM_ID_1)
        self.assertTrue(np.array_equal(doc.embedding, embedding))
        self.assertEqual(doc.id.vector_store_id, self.store_id)

        # Check underlying MongoDB mock stores Binary for embedding
        stored_doc = self.mock_client['photos_drive'][self.collection_name].find_one(
            {"_id": doc.id.object_id}
        )
        self.assertIsInstance(stored_doc["embedding"], Binary)

    def test_delete_documents_removes_from_mock(self):
        embedding = self._make_embedding(1.2)
        req = CreateMediaItemEmbeddingRequest(
            embedding=embedding,
            media_item_id=MOCK_MEDIA_ITEM_ID_1,
            date_taken=MOCK_DATE_TAKEN,
        )
        added_doc = self.store.add_media_item_embeddings([req])[0]

        # Delete the added document
        self.store.delete_media_item_embeddings([added_doc.id])
        deleted = self.mock_client['photos_drive'][self.collection_name].find_one(
            {"_id": added_doc.id.object_id}
        )
        self.assertIsNone(deleted)

    def test_delete_documents_wrong_store_id_raises(self):
        embedding = self._make_embedding(2.12)
        req = CreateMediaItemEmbeddingRequest(
            embedding=embedding,
            media_item_id=MOCK_MEDIA_ITEM_ID_1,
            date_taken=MOCK_DATE_TAKEN,
        )
        added_doc = self.store.add_media_item_embeddings([req])[0]

        wrong_id = MediaItemEmbeddingId(
            vector_store_id=ObjectId(), object_id=added_doc.id.object_id
        )
        with self.assertRaises(ValueError):
            self.store.delete_media_item_embeddings([wrong_id])

    def test_get_relevent_documents_returns_up_to_k(self):
        num_docs = 10
        reqs = [
            CreateMediaItemEmbeddingRequest(
                embedding=self._make_embedding(i),
                media_item_id=MOCK_MEDIA_ITEM_ID_1,
                date_taken=MOCK_DATE_TAKEN,
            )
            for i in range(num_docs)
        ]
        self.store.add_media_item_embeddings(reqs)

        query_embedding = self._make_embedding(3)
        results = self.store.get_relevent_media_item_embeddings(
            QueryMediaItemEmbeddingRequest(query_embedding, top_k=5)
        )
        self.assertEqual(len(results), 5)

    def test_get_relevent_documents_returns_data_correctly(self):
        embedding = self._make_embedding(0)
        added_doc = self.store.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=embedding,
                    media_item_id=MOCK_MEDIA_ITEM_ID_1,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )

        results = self.store.get_relevent_media_item_embeddings(
            QueryMediaItemEmbeddingRequest(embedding, top_k=1)
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, added_doc[0].id)
        np.testing.assert_array_almost_equal(results[0].embedding, embedding, decimal=6)
        self.assertEqual(results[0].media_item_id, MOCK_MEDIA_ITEM_ID_1)

    def _make_embedding(self, val=1.0):
        return np.full(self.embedding_dimensions, val, dtype=np.float32)
