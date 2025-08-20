from datetime import datetime, timezone
import unittest

from bson.objectid import ObjectId
import numpy as np

from photos_drive.shared.llm.vector_stores.base_vector_store import (
    CreateMediaItemEmbeddingRequest,
    QueryMediaItemEmbeddingRequest,
)
from photos_drive.shared.llm.vector_stores.distributed_vector_store import (
    DistributedVectorStore,
)
from photos_drive.shared.llm.vector_stores.mongo_db_vector_store import (
    MongoDbVectorStore,
)
from photos_drive.shared.llm.vector_stores.testing.mock_mongo_client import (
    MockMongoClient,
)
from photos_drive.shared.metadata.media_item_id import MediaItemId

MOCK_MEDIA_ITEM_ID_1 = MediaItemId(ObjectId(), ObjectId())

MOCK_MEDIA_ITEM_ID_2 = MediaItemId(ObjectId(), ObjectId())

MOCK_MEDIA_ITEM_ID_3 = MediaItemId(ObjectId(), ObjectId())

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0, tzinfo=timezone.utc)


class TestDistributedVectorStoreWithMongoDbVectorStore(unittest.TestCase):
    def setUp(self):
        # Create multiple mock clients and stores
        self.mock_client1 = MockMongoClient()
        self.mock_client2 = MockMongoClient()

        self.db_name = "photos_drive"
        self.collection_name = "test_embeddings"
        self.embedding_dim = 8

        self.store1_id = ObjectId()
        self.store2_id = ObjectId()

        self.store1 = MongoDbVectorStore(
            store_id=self.store1_id,
            mongodb_client=self.mock_client1,
            db_name=self.db_name,
            collection_name=self.collection_name,
            embedding_dimensions=self.embedding_dim,
        )

        self.store2 = MongoDbVectorStore(
            store_id=self.store2_id,
            mongodb_client=self.mock_client2,
            db_name=self.db_name,
            collection_name=self.collection_name,
            embedding_dimensions=self.embedding_dim,
        )

        self.distributed_store = DistributedVectorStore([self.store1, self.store2])

    def _make_embedding(self, val=1.0):
        return np.full(self.embedding_dim, val, dtype=np.float32)

    def test_get_store_id_raises(self):
        with self.assertRaises(NotImplementedError):
            self.distributed_store.get_store_id()

    def test_get_available_space_returns_sum(self):
        # Mock get_available_space on stores
        self.mock_client1['photos_drive'].set_db_stats(
            {
                'totalFreeStorageSize': 100,
            }
        )
        self.mock_client2['photos_drive'].set_db_stats(
            {
                'totalFreeStorageSize': 300,
            }
        )
        total = self.distributed_store.get_available_space()
        self.assertEqual(total, 400)

    def test_add_documents_distributes_evenly(self):
        self.mock_client1['photos_drive'].set_db_stats(
            {
                'totalFreeStorageSize': 2,
            }
        )
        self.mock_client2['photos_drive'].set_db_stats(
            {
                'totalFreeStorageSize': 3,
            }
        )

        requests = [
            CreateMediaItemEmbeddingRequest(
                embedding=self._make_embedding(i),
                media_item_id=MOCK_MEDIA_ITEM_ID_1,
                date_taken=MOCK_DATE_TAKEN,
            )
            for i in range(5)
        ]

        added_docs = self.distributed_store.add_media_item_embeddings(requests)

        # Check total docs returned == input docs
        self.assertEqual(len(added_docs), 5)

        # Check how many documents each store received via their internal _collection
        # docs
        count_store1_docs = len(
            self.mock_client1[self.db_name][self.collection_name]._documents
        )
        count_store2_docs = len(
            self.mock_client2[self.db_name][self.collection_name]._documents
        )

        self.assertEqual(count_store1_docs, 2)
        self.assertEqual(count_store2_docs, 3)

        # All DocumentId vector_store_id must match the store where stored
        store1_ids = {
            doc.id.vector_store_id
            for doc in added_docs
            if doc.id.vector_store_id == self.store1_id
        }
        store2_ids = {
            doc.id.vector_store_id
            for doc in added_docs
            if doc.id.vector_store_id == self.store2_id
        }
        self.assertTrue(len(store1_ids) > 0)
        self.assertTrue(len(store2_ids) > 0)
        self.assertEqual(len(store1_ids) + len(store2_ids), 2)  # IDs unique per store

    def test_add_documents_raises_when_not_enough_space(self):
        self.mock_client1['photos_drive'].set_db_stats(
            {
                'totalFreeStorageSize': 1,
            }
        )
        self.mock_client2['photos_drive'].set_db_stats(
            {
                'totalFreeStorageSize': 1,
            }
        )

        requests = [
            CreateMediaItemEmbeddingRequest(
                embedding=self._make_embedding(i),
                media_item_id=MOCK_MEDIA_ITEM_ID_1,
                date_taken=MOCK_DATE_TAKEN,
            )
            for i in range(3)
        ]  # 3 docs > 2 spaces
        with self.assertRaises(RuntimeError):
            self.distributed_store.add_media_item_embeddings(requests)

    def test_delete_documents_sends_correct_ids_to_stores(self):
        # Add some documents to stores directly for IDs
        doc1 = self.store1.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(0),
                    media_item_id=MOCK_MEDIA_ITEM_ID_1,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )[0]
        doc2 = self.store2.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(1),
                    media_item_id=MOCK_MEDIA_ITEM_ID_2,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )[0]

        self.distributed_store.delete_media_item_embeddings_by_media_item_ids(
            [MOCK_MEDIA_ITEM_ID_1, MOCK_MEDIA_ITEM_ID_2]
        )

        # Ensure that they are deleted
        self.assertIsNone(
            self.mock_client1[self.db_name][self.collection_name].find_one(
                {'_id': doc1.id.object_id}
            )
        )
        self.assertIsNone(
            self.mock_client2[self.db_name][self.collection_name].find_one(
                {'_id': doc2.id.object_id}
            )
        )

    def test_get_relevent_documents_aggregates_and_ranks(self):
        # Add docs with embeddings to store1 and store2
        embed1 = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
        embed2 = np.array([0, 1, 0, 0, 0, 0, 0, 0], dtype=np.float32)
        embed3 = np.array([0.5, 0.5, 0, 0, 0, 0, 0, 0], dtype=np.float32)
        self.store1.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=embed1,
                    media_item_id=MOCK_MEDIA_ITEM_ID_1,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )[0]
        self.store2.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=embed2,
                    media_item_id=MOCK_MEDIA_ITEM_ID_2,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )[0]
        self.store2.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=embed3,
                    media_item_id=MOCK_MEDIA_ITEM_ID_3,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )[0]

        results = self.distributed_store.get_relevent_media_item_embeddings(
            QueryMediaItemEmbeddingRequest(
                embedding=np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32),
                top_k=2,
            )
        )

        self.assertEqual(len(results), 2)

        # Results should be sorted by cosine similarity
        self.assertEqual(results[0].media_item_id, MOCK_MEDIA_ITEM_ID_1)
        self.assertEqual(results[1].media_item_id, MOCK_MEDIA_ITEM_ID_3)

    def test_get_relevent_documents_empty(self):
        # Query with no docs in stores should return empty list without error
        results = self.distributed_store.get_relevent_media_item_embeddings(
            QueryMediaItemEmbeddingRequest(
                embedding=np.ones(self.embedding_dim, dtype=np.float32), top_k=3
            )
        )
        self.assertEqual(results, [])

    def test_get_embeddings_by_media_item_ids_across_stores(self):
        # Add documents to both stores
        doc1 = self.store1.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(0),
                    media_item_id=MOCK_MEDIA_ITEM_ID_1,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )[0]
        doc2 = self.store2.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(1),
                    media_item_id=MOCK_MEDIA_ITEM_ID_2,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )[0]
        doc3 = self.store1.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(2),
                    media_item_id=MOCK_MEDIA_ITEM_ID_3,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )[0]

        # Query for all three documents from the distributed store
        requested_ids = [
            MOCK_MEDIA_ITEM_ID_1,
            MOCK_MEDIA_ITEM_ID_2,
            MOCK_MEDIA_ITEM_ID_3,
        ]
        results = self.distributed_store.get_embeddings_by_media_item_ids(requested_ids)

        # Assertions
        self.assertEqual(len(results), 3)
        retrieved_ids = {doc.media_item_id for doc in results}
        self.assertSetEqual(retrieved_ids, set(requested_ids))

        # Check the content of the retrieved documents
        retrieved_doc_1 = next(
            doc for doc in results if doc.media_item_id == MOCK_MEDIA_ITEM_ID_1
        )
        np.testing.assert_array_equal(retrieved_doc_1.embedding, doc1.embedding)

        retrieved_doc_2 = next(
            doc for doc in results if doc.media_item_id == MOCK_MEDIA_ITEM_ID_2
        )
        np.testing.assert_array_equal(retrieved_doc_2.embedding, doc2.embedding)

        retrieved_doc_3 = next(
            doc for doc in results if doc.media_item_id == MOCK_MEDIA_ITEM_ID_3
        )
        np.testing.assert_array_equal(retrieved_doc_3.embedding, doc3.embedding)

    def test_get_embeddings_by_media_item_ids_with_non_existent_ids(self):
        # Add one document to a store
        self.store1.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(0),
                    media_item_id=MOCK_MEDIA_ITEM_ID_1,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )

        # Query for a mix of existing and non-existent IDs
        non_existent_id = MediaItemId(ObjectId(), ObjectId())
        requested_ids = [MOCK_MEDIA_ITEM_ID_1, non_existent_id]
        results = self.distributed_store.get_embeddings_by_media_item_ids(requested_ids)

        # Assertions
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].media_item_id, MOCK_MEDIA_ITEM_ID_1)

    def test_get_embeddings_by_media_item_ids_empty_list(self):
        # Add some docs to ensure the stores are not empty
        self.store1.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(0),
                    media_item_id=MOCK_MEDIA_ITEM_ID_1,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )

        # Query with an empty list of IDs
        results = self.distributed_store.get_embeddings_by_media_item_ids([])

        # Assertions
        self.assertEqual(len(results), 0)

    def test_get_embeddings_by_media_item_ids_with_duplicates(self):
        # Add one document
        self.store1.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(0),
                    media_item_id=MOCK_MEDIA_ITEM_ID_1,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )[0]

        # Query with a list containing the same ID multiple times
        requested_ids = [MOCK_MEDIA_ITEM_ID_1, MOCK_MEDIA_ITEM_ID_1]
        results = self.distributed_store.get_embeddings_by_media_item_ids(requested_ids)

        # The function should still return only one result for that ID
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].media_item_id, MOCK_MEDIA_ITEM_ID_1)
