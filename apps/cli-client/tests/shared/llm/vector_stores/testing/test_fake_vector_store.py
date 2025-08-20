from datetime import datetime, timezone
import unittest

from bson.objectid import ObjectId
import numpy as np

from photos_drive.shared.llm.vector_stores.base_vector_store import (
    CreateMediaItemEmbeddingRequest,
    QueryMediaItemEmbeddingRequest,
)
from photos_drive.shared.llm.vector_stores.testing.fake_vector_store import (
    FakeVectorStore,
)
from photos_drive.shared.metadata.media_item_id import MediaItemId

MOCK_MEDIA_ITEM_ID_1 = MediaItemId(ObjectId(), ObjectId())
MOCK_MEDIA_ITEM_ID_2 = MediaItemId(ObjectId(), ObjectId())
MOCK_MEDIA_ITEM_ID_3 = MediaItemId(ObjectId(), ObjectId())

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0, tzinfo=timezone.utc)


class TestFakeVectorStore(unittest.TestCase):
    def setUp(self):
        self.store = FakeVectorStore()
        self.embedding_dim = 8

    def test_get_store_id_returns_same_id(self):
        store_id = self.store.get_store_id()
        self.assertIsInstance(store_id, ObjectId)

    def test_get_available_space_returns_large_number(self):
        self.assertEqual(self.store.get_available_space(), 10**8)

    def test_add_media_item_embeddings_adds_embeddings(self):
        req = CreateMediaItemEmbeddingRequest(
            embedding=self._make_embedding(1.0),
            media_item_id=MOCK_MEDIA_ITEM_ID_1,
            date_taken=MOCK_DATE_TAKEN,
        )
        added = self.store.add_media_item_embeddings([req])
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0].media_item_id, MOCK_MEDIA_ITEM_ID_1)
        self.assertTrue(np.allclose(added[0].embedding, req.embedding))

    def test_delete_media_item_embeddings_by_media_item_ids_removes_entries(self):
        self.store.add_media_item_embeddings(
            [
                CreateMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(1.0),
                    media_item_id=MOCK_MEDIA_ITEM_ID_1,
                    date_taken=MOCK_DATE_TAKEN,
                )
            ]
        )
        self.store.delete_media_item_embeddings_by_media_item_ids(
            [MOCK_MEDIA_ITEM_ID_1]
        )
        results = self.store.get_relevent_media_item_embeddings(
            QueryMediaItemEmbeddingRequest(embedding=self._make_embedding(1.0), top_k=1)
        )
        self.assertEqual(results, [])

    def test_delete_all_media_item_embeddings_clears_all(self):
        reqs = [
            CreateMediaItemEmbeddingRequest(
                embedding=self._make_embedding(i),
                media_item_id=MOCK_MEDIA_ITEM_ID_1,
                date_taken=MOCK_DATE_TAKEN,
            )
            for i in range(3)
        ]
        self.store.add_media_item_embeddings(reqs)
        self.store.delete_all_media_item_embeddings()
        self.assertEqual(
            self.store.get_relevent_media_item_embeddings(
                QueryMediaItemEmbeddingRequest(
                    embedding=self._make_embedding(1.0), top_k=3
                )
            ),
            [],
        )

    def test_get_relevent_media_item_embeddings_returns_sorted_results(self):
        reqs = [
            CreateMediaItemEmbeddingRequest(
                embedding=np.array([1.0, 0.0]),
                media_item_id=MOCK_MEDIA_ITEM_ID_1,
                date_taken=MOCK_DATE_TAKEN,
            ),
            CreateMediaItemEmbeddingRequest(
                embedding=np.array([0.0, 1.0]),
                media_item_id=MOCK_MEDIA_ITEM_ID_2,
                date_taken=MOCK_DATE_TAKEN,
            ),
            CreateMediaItemEmbeddingRequest(
                embedding=np.array([0.5, 0.5]),
                media_item_id=MOCK_MEDIA_ITEM_ID_3,
                date_taken=MOCK_DATE_TAKEN,
            ),
        ]
        self.store = FakeVectorStore()
        self.store.add_media_item_embeddings(reqs)

        query = np.array([1.0, 0.0])
        results = self.store.get_relevent_media_item_embeddings(
            QueryMediaItemEmbeddingRequest(embedding=query, top_k=2)
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].media_item_id, MOCK_MEDIA_ITEM_ID_1)
        self.assertEqual(results[1].media_item_id, MOCK_MEDIA_ITEM_ID_3)

    def test_get_relevent_media_item_embeddings_returns_empty_for_zero_vector(self):
        req = CreateMediaItemEmbeddingRequest(
            embedding=self._make_embedding(1.0),
            media_item_id=MOCK_MEDIA_ITEM_ID_1,
            date_taken=MOCK_DATE_TAKEN,
        )
        self.store.add_media_item_embeddings([req])
        zero_vector = np.zeros(self.embedding_dim)
        results = self.store.get_relevent_media_item_embeddings(
            QueryMediaItemEmbeddingRequest(embedding=zero_vector, top_k=1)
        )
        self.assertEqual(results, [])

    def _make_embedding(self, val=1.0):
        return np.full(self.embedding_dim, val, dtype=np.float32)
