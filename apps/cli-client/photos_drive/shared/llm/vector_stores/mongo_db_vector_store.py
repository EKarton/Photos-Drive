from datetime import datetime
import logging
import pymongo
from typing import Any, Mapping, cast, override
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
    QueryMediaItemEmbeddingRequest,
    UpdateMediaItemEmbeddingRequest,
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
                    },
                    {
                        'type': 'filter',
                        'path': 'date_taken',
                    },
                    {
                        'type': 'filter',
                        'path': 'media_item_id',
                    },
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
            data_object = {
                "embedding": self.__get_mongodb_vector(req.embedding),
                "media_item_id": media_item_id_to_string(req.media_item_id),
                "date_taken": req.date_taken,
            }
            documents_to_insert.append(data_object)
        result = self._collection.insert_many(documents_to_insert)

        # Build the return values
        added_docs = []
        for req, inserted_id in zip(requests, result.inserted_ids):
            added_docs.append(
                MediaItemEmbedding(
                    id=MediaItemEmbeddingId(
                        vector_store_id=self._store_id,
                        object_id=inserted_id,
                    ),
                    embedding=req.embedding,
                    media_item_id=req.media_item_id,
                    date_taken=req.date_taken,
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
                "_id": embedding_id.object_id,
            }
        )
        if doc is None:
            raise ValueError(f"Cannot find embedding for {embedding_id}")

        return self.__parse_raw_document_to_media_item_embedding_obj(doc)

    @override
    def get_relevent_media_item_embeddings(
        self, query: QueryMediaItemEmbeddingRequest
    ) -> list[MediaItemEmbedding]:
        pipeline = []

        filter_obj: dict[str, Any] = {}
        if query.start_date_taken or query.end_date_taken:
            date_filter = {}
            if query.start_date_taken:
                date_filter["$gte"] = query.start_date_taken
            if query.end_date_taken:
                date_filter["$lte"] = query.end_date_taken
            filter_obj['date_taken'] = date_filter

        if query.within_media_item_ids:
            filter_obj['media_item_id'] = {
                "$in": [
                    media_item_id_to_string(media_item_id)
                    for media_item_id in query.within_media_item_ids
                ]
            }

        # First do vector search
        pipeline.append(
            {
                "$vectorSearch": {
                    "queryVector": self.__get_mongodb_vector(query.embedding),
                    "path": "embedding",
                    "numCandidates": query.top_k * 5,
                    "limit": query.top_k,
                    "index": self._embedding_index_name,
                    "filter": filter_obj,
                }
            }
        )

        docs = []
        for doc in self._collection.aggregate(pipeline):
            docs.append(self.__parse_raw_document_to_media_item_embedding_obj(doc))
        return docs

    @override
    def delete_all_media_item_embeddings(self):
        self._collection.delete_many({})

    @override
    def update_media_item_embeddings(
        self, requests: list[UpdateMediaItemEmbeddingRequest]
    ):
        operations: list[pymongo.UpdateOne] = []
        for request in requests:
            filter_query: Mapping = {
                "_id": request.embedding_id.object_id,
            }

            set_query: Mapping = {"$set": {}, "$unset": {}}

            if request.new_embedding:
                set_query["$set"]['embedding'] = self.__get_mongodb_vector(
                    request.new_embedding
                )

            if request.new_media_item_id:
                set_query["$set"]['media_item_id'] = media_item_id_to_string(
                    request.new_media_item_id
                )

            if request.new_date_taken:
                set_query["$set"]['date_taken'] = request.new_date_taken

            operations.append(
                pymongo.UpdateOne(filter=filter_query, update=set_query, upsert=False)
            )

        print(operations)

        result = self._collection.bulk_write(operations)
        if result.matched_count != len(operations):
            raise ValueError(
                f"Unable to update all embeddings: {result.matched_count} "
                + f"vs {len(operations)}"
            )

    def __get_mongodb_vector(self, embedding: np.ndarray) -> Binary:
        return Binary.from_vector(embedding.tolist(), BinaryVectorDtype.FLOAT32)

    def __get_embedding_np_from_mongo(self, raw_embedding: Binary) -> np.ndarray:
        return np.array(raw_embedding.as_vector().data, dtype=np.float32)

    def __parse_raw_document_to_media_item_embedding_obj(
        self, raw_item: Mapping[str, Any]
    ) -> MediaItemEmbedding:
        date_taken = None
        if 'date_taken' in raw_item and raw_item['date_taken']:
            date_taken = cast(datetime, raw_item['date_taken'])
        else:
            date_taken = datetime(1970, 1, 1)

        return MediaItemEmbedding(
            id=MediaItemEmbeddingId(
                vector_store_id=self.get_store_id(), object_id=raw_item['_id']
            ),
            embedding=self.__get_embedding_np_from_mongo(raw_item["embedding"]),
            media_item_id=parse_string_to_media_item_id(raw_item["media_item_id"]),
            date_taken=date_taken,
        )
