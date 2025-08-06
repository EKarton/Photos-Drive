import logging
from typing import override
from photos_drive.shared.metadata.media_item_id import (
    media_item_id_to_string,
    parse_string_to_media_item_id,
)
from pymongo import MongoClient
from bson.objectid import ObjectId
import numpy as np
from pymongo.operations import SearchIndexModel
from pymongo.errors import CollectionInvalid
from bson.binary import Binary, BinaryVectorDtype

from .testing.mock_mongo_client import MockMongoClient
from .base_vector_store import (
    BaseVectorStore,
    CreateMediaItemEmbeddingRequest,
    MediaItemEmbedding,
    MediaItemEmbeddingId,
)

logger = logging.getLogger(__name__)

BYTES_512MB = 536870912

EMBEDDING_INDEX_NAME = 'vector_index'


class MongoDbVectorStore(BaseVectorStore):
    def __init__(
        self,
        store_id: ObjectId,
        mongodb_client: MongoClient | MockMongoClient,
        db_name: str,
        collection_name: str,
        embedding_dimensions: int,
        embedding_index_name: str = EMBEDDING_INDEX_NAME,
    ):
        self._store_id = store_id
        self._mongodb_client = mongodb_client
        self._db_name = db_name
        self._collection_name = collection_name
        self._collection = mongodb_client[db_name][collection_name]
        self._embedding_dimensions = embedding_dimensions
        self._embedding_index_name = embedding_index_name

        if not any(
            [
                index["name"] == self._embedding_index_name
                for index in self._collection.list_search_indexes()
            ]
        ):
            self.__create_search_index()

    def __create_search_index(self):
        try:
            self._mongodb_client[self._db_name].create_collection(self._collection_name)
        except CollectionInvalid:
            pass
        search_index_model = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "similarity": "dotProduct",
                        "numDimensions": self._embedding_dimensions,
                        'quantization': 'binary',
                    }
                ]
            },
            name=self._embedding_index_name,
            type="vectorSearch",
        )
        self._collection.create_search_index(model=search_index_model)
        logger.debug(f'Created search index {self._embedding_index_name}')

    @override
    def get_store_id(self) -> ObjectId:
        return self._store_id

    @override
    def get_available_space(self) -> int:
        db = self._mongodb_client[self._db_name]
        db_stats = db.command({'dbStats': 1, 'freeStorage': 1})
        raw_total_free_storage = db_stats.get("totalFreeStorageSize", 0)

        if raw_total_free_storage == 0:
            # Fallback: just use arbitrary 512MB limit if unavailable
            raw_total_free_storage = BYTES_512MB - db_stats.get("storageSize", 0)

        return raw_total_free_storage

    @override
    def add_media_item_embeddings(
        self, requests: list[CreateMediaItemEmbeddingRequest]
    ) -> list[MediaItemEmbedding]:
        documents_to_insert = []
        for req in requests:
            documents_to_insert.append(
                {
                    "embedding": self.__get_mongodb_vector(req.embedding),
                    "media_item_id": media_item_id_to_string(req.media_item_id),
                }
            )
        result = self._collection.insert_many(documents_to_insert)

        # Build the return values
        added_docs = []
        for req, inserted_id in zip(requests, result.inserted_ids):
            doc_id = MediaItemEmbeddingId(
                vector_store_id=self._store_id,
                object_id=inserted_id,
            )
            added_docs.append(
                MediaItemEmbedding(
                    id=doc_id,
                    embedding=req.embedding,
                    media_item_id=req.media_item_id,
                )
            )
        return added_docs

    @override
    def delete_media_item_embeddings(self, ids: list[MediaItemEmbeddingId]):
        store_ids = [id.vector_store_id for id in ids]
        if not all(sid == self.get_store_id() for sid in store_ids):
            raise ValueError('Some IDs do not belong to this vector store')

        object_ids = [id.object_id for id in ids]
        self._collection.delete_many({"_id": {"$in": object_ids}})

    @override
    def get_embedding_by_id(
        self, embedding_id: MediaItemEmbeddingId
    ) -> MediaItemEmbedding:
        doc = self._collection.find_one(
            {
                "_id": embedding_id.vector_store_id,
            }
        )
        if doc is None:
            raise ValueError(f"Cannot find embedding for {embedding_id}")

        return MediaItemEmbedding(
            id=embedding_id,
            embedding=self.__get_embedding_np_from_mongo(doc["embedding"]),
            media_item_id=parse_string_to_media_item_id(doc.get("media_item_id")),
        )

    @override
    def get_relevent_media_item_embeddings(
        self, embedding: np.ndarray, k: int
    ) -> list[MediaItemEmbedding]:
        pipeline = [
            {
                "$vectorSearch": {
                    "queryVector": self.__get_mongodb_vector(embedding),
                    "path": "embedding",
                    "numCandidates": k * 5,  # can tune
                    "limit": k,
                    "index": self._embedding_index_name,
                }
            }
        ]
        docs = []
        for doc in self._collection.aggregate(pipeline):
            doc_id = MediaItemEmbeddingId(
                vector_store_id=self._store_id, object_id=doc["_id"]
            )
            docs.append(
                MediaItemEmbedding(
                    id=doc_id,
                    embedding=self.__get_embedding_np_from_mongo(doc["embedding"]),
                    media_item_id=parse_string_to_media_item_id(
                        doc.get("media_item_id")
                    ),
                )
            )
        return docs

    def __get_mongodb_vector(self, embedding: np.ndarray) -> Binary:
        return Binary.from_vector(embedding.tolist(), BinaryVectorDtype.FLOAT32)

    def __get_embedding_np_from_mongo(self, raw_embedding: Binary) -> np.ndarray:
        return np.array(raw_embedding.as_vector().data, dtype=np.float32)

    @override
    def delete_all_media_item_embeddings(self):
        self._collection.delete_many({})
