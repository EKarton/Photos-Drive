from unittest.mock import Mock

import mongomock


def create_mock_mongo_client(
    total_free_storage_size: int = 1000,
    storage_size: int = 0,
    objects: int = 0,
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
    mock_client["photos_drive"].command = Mock(  # type: ignore
        return_value={
            "totalFreeStorageSize": total_free_storage_size,
            "storageSize": storage_size,
            'objects': objects,
        }
    )
    collection = mock_client['photos_drive']['media_items']
    collection.list_search_indexes = Mock(return_value=[])  # type: ignore

    mock_session = Mock()
    mock_session.__bool__ = Mock(return_value=False)
    mock_session.start_transaction = Mock()
    mock_session.commit_transaction = Mock()
    mock_session.abort_transaction = Mock()
    mock_session.end_session = Mock()

    mock_client.start_session = Mock(return_value=mock_session)  # type: ignore

    return mock_client
