from typing_extensions import override

from bson.objectid import ObjectId
import numpy as np

from photos_drive.shared.llm.vector_stores.base_vector_store import (
    BaseVectorStore,
    CreateMediaItemEmbeddingRequest,
    MediaItemEmbedding,
    MediaItemEmbeddingId,
    QueryMediaItemEmbeddingRequest,
)

DEFAULT_VECTOR_STORE_ID = ObjectId()


class FakeVectorStore(BaseVectorStore):
    '''Represents a fake vector store. It's for testing purposes.'''

    def __init__(self, store_id=DEFAULT_VECTOR_STORE_ID):
        self.__store_id: ObjectId = store_id
        self.__id_to_embeddings: dict[MediaItemEmbeddingId, MediaItemEmbedding] = {}

    @override
    def get_store_id(self) -> ObjectId:
        return self.__store_id

    @override
    def get_available_space(self) -> int:
        return 10**8

    @override
    def add_media_item_embeddings(
        self, requests: list[CreateMediaItemEmbeddingRequest]
    ) -> list[MediaItemEmbedding]:
        new_embeddings = []
        for request in requests:
            id = self.__generate_unique_media_item_embedding_id()
            new_embedding = MediaItemEmbedding(
                id=id,
                embedding=request.embedding,
                media_item_id=request.media_item_id,
                date_taken=request.date_taken,
            )
            self.__id_to_embeddings[id] = new_embedding
            new_embeddings.append(new_embedding)
        return new_embeddings

    @override
    def delete_media_item_embeddings(self, ids: list[MediaItemEmbeddingId]):
        for id in ids:
            self.__id_to_embeddings.pop(id, None)

    @override
    def get_relevent_media_item_embeddings(
        self, query: QueryMediaItemEmbeddingRequest
    ) -> list[MediaItemEmbedding]:
        if not self.__id_to_embeddings:
            return []

        query_vec = query.embedding
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []
        query_vec = query_vec / query_norm

        # Compute cosine similarity for all stored embeddings
        scored_embeddings = []
        for media_embedding in self.__id_to_embeddings.values():
            stored_vec = media_embedding.embedding
            stored_norm = np.linalg.norm(stored_vec)
            stored_vec = stored_vec / stored_norm
            cosine_sim = np.dot(query_vec, stored_vec)
            scored_embeddings.append((cosine_sim, media_embedding))

        # Get top k by descending similarity
        top_k = sorted(scored_embeddings, key=lambda x: x[0], reverse=True)[
            : query.top_k
        ]

        return [embedding for _, embedding in top_k]

    @override
    def delete_all_media_item_embeddings(self):
        self.__id_to_embeddings.clear()

    @override
    def get_embedding_by_id(self, embedding_id):
        return self.__id_to_embeddings[embedding_id]

    @override
    def update_media_item_embeddings(self, requests):
        for request in requests:
            original_embedding = self.__id_to_embeddings[request.embedding_id]

            date_taken = original_embedding.date_taken
            if request.new_date_taken:
                date_taken = request.new_date_taken

            media_item_id = original_embedding.media_item_id
            if request.new_media_item_id:
                media_item_id = request.new_media_item_id

            embedding = original_embedding.embedding
            if request.new_embedding:
                embedding = request.new_embedding

            self.__id_to_embeddings[request.embedding_id] = MediaItemEmbedding(
                id=request.embedding_id,
                embedding=embedding,
                media_item_id=media_item_id,
                date_taken=date_taken,
            )

    def __generate_unique_media_item_embedding_id(self) -> MediaItemEmbeddingId:
        id = MediaItemEmbeddingId(ObjectId(), ObjectId())
        while id in self.__id_to_embeddings:
            id = MediaItemEmbeddingId(ObjectId(), ObjectId())

        return id
