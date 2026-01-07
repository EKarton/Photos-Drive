from pymongo.mongo_client import MongoClient

from photos_drive.shared.config.config import (
    MongoDbVectorStoreConfig,
    VectorStoreConfig,
)
from photos_drive.shared.llm.vector_stores.base_vector_store import BaseVectorStore
from photos_drive.shared.llm.vector_stores.mongo_db_vector_store import (
    MongoDbVectorStore,
)


def config_to_vector_store(
    config: VectorStoreConfig, embedding_dimensions=768
) -> BaseVectorStore:
    if isinstance(config, MongoDbVectorStoreConfig):
        return config_to_mongodb_vector_store(config, embedding_dimensions)
    else:
        raise NotImplementedError(f'{type(config)} not supported yet')


def config_to_mongodb_vector_store(
    config: MongoDbVectorStoreConfig,
    embedding_dimensions=768,
) -> MongoDbVectorStore:
    return MongoDbVectorStore(
        store_id=config.id,
        store_name=config.name,
        mongodb_client=MongoClient(config.read_write_connection_string),
        db_name='photos_drive',
        collection_name="media_item_embeddings",
        embedding_dimensions=embedding_dimensions,
    )
