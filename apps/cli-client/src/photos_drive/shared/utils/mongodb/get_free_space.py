from pymongo.mongo_client import MongoClient

from photos_drive.shared.features.llm.vector_stores.testing.mock_mongo_client import (
    MockMongoClient,
)

BYTES_512MB = 536870912


def get_free_space(mongodb_client: MongoClient | MockMongoClient) -> int:
    '''
    Returns the amount of free space in a Mongodb client

    Args:
        mongodb_client (MongoClient | MockMongoClient):
            The MongoDB client

    Returns:
        int: The amount of space left
    '''
    db = mongodb_client["photos_drive"]
    db_stats = db.command({'dbStats': 1, 'freeStorage': 1})
    raw_total_free_storage = db_stats["totalFreeStorageSize"]

    # Handle case of free tier: they return 0 for `totalFreeStorageSize`
    # even though it is 512 MB
    free_space = raw_total_free_storage
    if raw_total_free_storage == 0:
        free_space = BYTES_512MB - db_stats["storageSize"]

    return free_space
