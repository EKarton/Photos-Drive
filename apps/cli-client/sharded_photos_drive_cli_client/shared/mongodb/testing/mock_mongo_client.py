import mongomock
from unittest.mock import Mock


def create_mock_mongo_client(
    total_free_storage_size: int = 1000,
) -> mongomock.MongoClient:
    '''
    Creates a fake MongoDB Client with fake 'totalFreeStorageSize' stats
    that you can use to build an in-memory MongoDB database.

    Args:
        total_free_storage_size (int): The total free storage size

    Returns:
        mongomock.MongoClient: A fake MongoDB client
    '''
    mock_client: mongomock.MongoClient = mongomock.MongoClient()
    mock_client["sharded_google_photos"].command = Mock(  # type: ignore
        return_value={"totalFreeStorageSize": total_free_storage_size}
    )

    return mock_client
