from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
from bson.objectid import ObjectId
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
    Represents an embedding for a media item

    Attributes:
        id (DocumentId): The document ID
        embedding (np.ndarray): The embedding
        media_item_id (MediaItemId): The ID of the media item
    '''

    id: MediaItemEmbeddingId
    embedding: np.ndarray
    media_item_id: MediaItemId


@dataclass(frozen=True)
class CreateMediaItemEmbeddingRequest:
    '''
    Represents a request to add a media item embedding in the vector store

    Attributes:
        embedding (np.ndarray): The embedding
        media_item_id (MediaItemId): The ID of the media item
    '''

    embedding: np.ndarray
    media_item_id: MediaItemId


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
    def delete_media_item_embeddings(self, ids: list[MediaItemEmbeddingId]):
        '''
        Deletes a list of media item embeddings

        Args:
            ids (list[MediaItemEmbeddingId]): A list of embeddings by their
                IDs to delete from the store
        '''

    @abstractmethod
    def get_relevent_media_item_embeddings(
        self, embedding: np.ndarray, k: int
    ) -> list[MediaItemEmbedding]:
        '''
        Returns the top K relevent media item embeddings given an embedding.

        Args:
            embedding (np.ndarray): An embedding
            k (int): The top K media item embeddings to fetch

        Returns:
            list[MediaItemEmbedding]: A list of media item embeddings
        '''

    @abstractmethod
    def get_embedding_by_id(
        self, embedding_id: MediaItemEmbeddingId
    ) -> MediaItemEmbedding:
        '''
        Returns the embeddings from an embedding ID

        Args:
            embedding_id (MediaItemEmbeddingId): The embedding ID

        Returns:
            MediaItemEmbedding: the embedding
        '''

    @abstractmethod
    def delete_all_media_item_embeddings(self):
        '''
        Deletes all media item embeddings
        '''
