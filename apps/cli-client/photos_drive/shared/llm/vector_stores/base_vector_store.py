from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bson.objectid import ObjectId
import numpy as np

from photos_drive.shared.metadata.media_item_id import MediaItemId


@dataclass(frozen=True)
class MediaItemEmbeddingId:
    """
    Represents the ID of a media item embedding.
    Since embeddings are distributed across different vector stores, it consists of a
    vector store ID and the object ID.

    Attributes:
        vector_store_id (ObjectId): The ID of the vector store that it is saved under.
        object_id (ObjectId): The object ID of the document
    """

    vector_store_id: ObjectId
    object_id: ObjectId


def parse_string_to_embedding_id(value: str) -> MediaItemEmbeddingId:
    '''
    Parses and converts a string into an embedding ID.

    Args:
        value (str): The string must be in this format: 'abc:123'

    Returns:
        MediaItemEmbeddingId: The media item ID.
    '''
    vector_store_id, object_id = value.split(":")
    return MediaItemEmbeddingId(ObjectId(vector_store_id), ObjectId(object_id))


def embedding_id_to_string(embedding_id: MediaItemEmbeddingId) -> str:
    '''
    Parses and converts an embedding ID to a string.

    Args:
        embedding_id (MediaItemEmbeddingId): The embedding ID.

    Returns:
        string: The embedding ID in string form.
    '''
    return f"{embedding_id.vector_store_id}:{embedding_id.object_id}"


@dataclass(frozen=True)
class MediaItemEmbedding:
    '''
    Represents an embedding for a media item.

    Attributes:
        id (DocumentId): The document ID.
        embedding (np.ndarray): The embedding.
        media_item_id (MediaItemId): The ID of the media item.
        date_taken (datetime): The date of which this media item was taken.
    '''

    id: MediaItemEmbeddingId
    embedding: np.ndarray
    media_item_id: MediaItemId
    date_taken: datetime


@dataclass(frozen=True)
class CreateMediaItemEmbeddingRequest:
    '''
    Represents a request to add a media item embedding in the vector store.

    Attributes:
        embedding (np.ndarray): The embedding.
        media_item_id (MediaItemId): The ID of the media item.
        date_taken (datetime): The date of which the media item was taken.
    '''

    embedding: np.ndarray
    media_item_id: MediaItemId
    date_taken: datetime


@dataclass(frozen=True)
class UpdateMediaItemEmbeddingRequest:
    '''
    Represents a request to update a media item embedding in the vector store

    Attributes:
        embedding_id (MediaItemEmbeddingId): The ID to the media item embedding
        new_embedding Optional[np.ndarray]: A new embedding, if it is set
        new_media_item_id (Optional[MediaItemId]): The new MediaItemId, if it is set
        new_date_taken (Optional[datetime]): The new date taken, if it is set
    '''

    embedding_id: MediaItemEmbeddingId
    new_embedding: Optional[np.ndarray] = None
    new_media_item_id: Optional[MediaItemId] = None
    new_date_taken: Optional[datetime] = None


@dataclass(frozen=True)
class QueryMediaItemEmbeddingRequest:
    '''
    Represents a request to query the vector store

    Attributes:
        embedding (np.darray): The embedding to vector search in the vector store
        start_date_taken (Optional[datetime]): The earliest date to consider in the
            vector search
        end_date_taken (Optional[datetime]): The latest date to consider in the
            vector search
        within_media_item_ids (Optional[list[MediaItemId]]): The list of media item IDs
            to consider in the vector search
        top_k (int): The number of candidates to return
    '''

    embedding: np.ndarray
    start_date_taken: Optional[datetime] = None
    end_date_taken: Optional[datetime] = None
    within_media_item_ids: Optional[list[MediaItemId]] = None
    top_k: int = 5


class BaseVectorStore(ABC):
    '''
    Represents the base vector store.

    All image vector stores must extend from this class.
    '''

    @abstractmethod
    def get_store_id(self) -> ObjectId:
        '''
        Returns a unique store ID for this store.
        '''

    @abstractmethod
    def get_store_name(self) -> str:
        '''
        Returns the name for this store
        '''

    @abstractmethod
    def get_available_space(self) -> int:
        '''
        Returns the available space left in this store.
        '''

    @abstractmethod
    def add_media_item_embeddings(
        self, requests: list[CreateMediaItemEmbeddingRequest]
    ) -> list[MediaItemEmbedding]:
        '''
        Creates a list of embeddings

        Args:
            requests (list[CreateMediaItemEmbeddingRequest]): A list of
                embeddings to add to the store
        '''

    @abstractmethod
    def delete_media_item_embeddings_by_media_item_ids(
        self, media_item_ids: list[MediaItemId]
    ):
        '''
        Deletes a list of media item embeddings by its media item IDs

        Args:
            media_item_ids (list[MediaItemId]): A list of media item IDs
        '''

    @abstractmethod
    def get_relevent_media_item_embeddings(
        self, query: QueryMediaItemEmbeddingRequest
    ) -> list[MediaItemEmbedding]:
        '''
        Returns the top K relevent media item embeddings given an embedding.

        Args:
            query (QueryMediaItemEmbeddingRequest): The query

        Returns:
            list[MediaItemEmbedding]: A list of media item embeddings
        '''

    @abstractmethod
    def get_embeddings_by_media_item_ids(
        self, media_item_ids: list[MediaItemId]
    ) -> list[MediaItemEmbedding]:
        '''
        Returns the embeddings from a list of media item IDs

        Args:
            media_item_ids (list[MediaItemId]): A list of media item IDs to fetch for

        Returns:
            list[MediaItemEmbedding]: A list of embeddings
        '''

    @abstractmethod
    def delete_all_media_item_embeddings(self):
        '''
        Deletes all media item embeddings
        '''
