import logging
from typing import List, Tuple, override
import numpy as np
from bson.objectid import ObjectId

from .base_vector_store import (
    BaseVectorStore,
    MediaItemEmbedding,
    MediaItemEmbeddingId,
    CreateMediaItemEmbeddingRequest,
)

logger = logging.getLogger(__name__)


class DistributedVectorStore(BaseVectorStore):
    '''Represents a distributed image vector store'''

    def __init__(self, stores: List[BaseVectorStore]):
        self.stores = stores

    @override
    def get_store_id(self) -> ObjectId:
        raise NotImplementedError("There is no object ID for this store")

    @override
    def get_available_space(self) -> int:
        return sum(store.get_available_space() for store in self.stores)

    @override
    def add_media_item_embeddings(
        self, requests: List[CreateMediaItemEmbeddingRequest]
    ) -> List[MediaItemEmbedding]:
        # 1. Query all available spaces
        spaces = [store.get_available_space() for store in self.stores]
        total_space = sum(spaces)
        total_docs = len(requests)
        logger.info(
            f"Adding {total_docs} documents to the distributed store across "
            + f"{len(self.stores)} vector stores."
        )

        if total_docs > total_space:
            raise RuntimeError(
                "Not enough space in distributed vector stores to add all documents."
            )

        # 2. Distribute as evenly as possible, proportional to available space
        # list of doc indices for each store
        assignments: list[list[int]] = [[] for _ in self.stores]

        # Sort stores descending by space, to better spread
        store_infos = sorted(list(enumerate(spaces)), key=lambda x: -x[1])

        doc_idx = 0
        space_left_per_store = list(spaces)
        # Round robin, but weighted by available space
        while doc_idx < total_docs:
            # Re-sort as available space changes
            store_infos = sorted(
                [(i, space_left_per_store[i]) for i in range(len(self.stores))],
                key=lambda x: -x[1],
            )
            for i, avail_space in store_infos:
                if doc_idx >= total_docs:
                    break
                if avail_space > 0:
                    assignments[i].append(doc_idx)
                    space_left_per_store[i] -= 1
                    doc_idx += 1

        # 3. Actually add to each store and collect the Document objects
        result_docs = []
        for store_idx, doc_indices in enumerate(assignments):
            store = self.stores[store_idx]
            sub_requests = [requests[idx] for idx in doc_indices]

            # It's important to let each store assign its own vector_store_id in
            # DocumentId so we patch that here if necessary.
            docs = store.add_media_item_embeddings(sub_requests)
            result_docs.extend(docs)
        return result_docs

    @override
    def delete_media_item_embeddings(self, ids: List[MediaItemEmbeddingId]):
        # Group ids by their vector_store_id
        store_map: dict[ObjectId, list[MediaItemEmbeddingId]] = {}
        for doc_id in ids:
            store_map.setdefault(doc_id.vector_store_id, []).append(doc_id)

        for store in self.stores:
            store_id = store.get_store_id()
            if store_id in store_map:
                store.delete_media_item_embeddings(store_map[store_id])

    @override
    def get_relevent_media_item_embeddings(
        self, embedding: np.ndarray, k: int
    ) -> List[MediaItemEmbedding]:
        all_results: list[MediaItemEmbedding] = []
        for store in self.stores:
            docs = store.get_relevent_media_item_embeddings(embedding, k)
            all_results.extend(docs)

        # Compute similarities (cosine) and return top K
        # Assuming all embedding vectors are normalized or can be compared with np.dot
        doc_sims: list[Tuple[float, MediaItemEmbedding]] = []
        for doc in all_results:
            doc_emb = doc.embedding
            sim = np.dot(embedding, doc_emb) / (
                np.linalg.norm(embedding) * np.linalg.norm(doc_emb) + 1e-10
            )
            doc_sims.append((sim, doc))
        doc_sims.sort(reverse=True, key=lambda t: t[0])
        top_docs = [t[1] for t in doc_sims[:k]]
        return top_docs

    @override
    def get_embedding_by_id(
        self, embedding_id: MediaItemEmbeddingId
    ) -> MediaItemEmbedding:
        for store in self.stores:
            if store.get_store_id() == embedding_id.vector_store_id:
                print("Hehehe")
                return store.get_embedding_by_id(embedding_id)
        raise ValueError(f'Unable to find embedding {embedding_id}')

    @override
    def delete_all_media_item_embeddings(self):
        for store in self.stores:
            store.delete_all_media_item_embeddings()
