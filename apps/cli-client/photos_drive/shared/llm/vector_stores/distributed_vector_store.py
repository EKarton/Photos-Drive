import logging
from typing import List, Tuple

from bson.objectid import ObjectId
import numpy as np
from typing_extensions import override

from photos_drive.shared.llm.vector_stores.base_vector_store import (
    BaseVectorStore,
    CreateMediaItemEmbeddingRequest,
    MediaItemEmbedding,
    QueryMediaItemEmbeddingRequest,
)
from photos_drive.shared.metadata.media_item_id import (
    MediaItemId,
)

logger = logging.getLogger(__name__)


class DistributedVectorStore(BaseVectorStore):
    '''Represents a distributed image vector store'''

    def __init__(self, stores: List[BaseVectorStore]):
        self.stores = stores
        self._store_id_to_store: dict[ObjectId, BaseVectorStore] = {
            store.get_store_id(): store for store in stores
        }

    @override
    def get_store_id(self) -> ObjectId:
        raise NotImplementedError("There is no object ID for this store")

    @override
    def get_store_name(self) -> str:
        raise NotImplementedError("There is no name for this store")

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
    def delete_media_item_embeddings_by_media_item_ids(
        self, media_item_ids: list[MediaItemId]
    ):
        for store in self.stores:
            store.delete_media_item_embeddings_by_media_item_ids(media_item_ids)

    @override
    def get_relevent_media_item_embeddings(
        self, query: QueryMediaItemEmbeddingRequest
    ) -> List[MediaItemEmbedding]:
        all_results: list[MediaItemEmbedding] = []
        for store in self.stores:
            docs = store.get_relevent_media_item_embeddings(query)
            all_results.extend(docs)

        # Compute similarities (cosine) and return top K
        # Assuming all embedding vectors are normalized or can be compared with np.dot
        doc_sims: list[Tuple[float, MediaItemEmbedding]] = []
        for doc in all_results:
            doc_emb = doc.embedding
            sim = np.dot(query.embedding, doc_emb) / (
                np.linalg.norm(query.embedding) * np.linalg.norm(doc_emb) + 1e-10
            )
            doc_sims.append((sim, doc))
        doc_sims.sort(reverse=True, key=lambda t: t[0])
        top_docs = [t[1] for t in doc_sims[: query.top_k]]
        return top_docs

    @override
    def get_embeddings_by_media_item_ids(
        self, media_item_ids: list[MediaItemId]
    ) -> list[MediaItemEmbedding]:
        embeddings: list[MediaItemEmbedding] = []
        for store in self.stores:
            embeddings += store.get_embeddings_by_media_item_ids(media_item_ids)
        return embeddings

    @override
    def delete_all_media_item_embeddings(self):
        for store in self.stores:
            store.delete_all_media_item_embeddings()
