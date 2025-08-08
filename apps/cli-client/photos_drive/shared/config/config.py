from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from bson.objectid import ObjectId
from google.oauth2.credentials import Credentials

from photos_drive.shared.metadata.album_id import AlbumId


@dataclass(frozen=True)
class MongoDbConfig:
    '''
    A data class that encapsulates the MongoDB configurations.

    Attributes:
        id (ObjectId): The ID of this account.
        name (str): The name of the account.
        read_write_connection_string (str): The connection string to the MongoDB
            instance with read-write permissions.
        read_connection_string (str): The connection string to the MongoDB instance
            with only read permissions.
    '''

    id: ObjectId
    name: str
    read_write_connection_string: str
    read_only_connection_string: str


@dataclass(frozen=True)
class AddMongoDbConfigRequest:
    '''
    A data class that represents a request to add a new MongoDB configuration.

    Attributes:
        name (str): The name of the account
        read_write_connection_string (str): The connection string to the MongoDB
            instance with read-write permissions.
        read_connection_string (str): The connection string to the MongoDB instance
            with only read permissions.
    '''

    name: str
    read_write_connection_string: str
    read_only_connection_string: str


@dataclass(frozen=True)
class UpdateMongoDbConfigRequest:
    '''
    A data class that represents a request to update an existing MongoDB configuration.

    Attributes:
        id (ObjectId): The ID of the MongoDB config.
        new_name (Optional[str]): The new name of the account, if present.
        new_read_write_connection_string (Optional[str]): The new connection string to
            the MongoDB instance with read-write permissions, if present.
        new_read_connection_string (Optional[str]): The new connection string to the
            MongoDB instance with only read permissions, if present.
    '''

    id: ObjectId
    new_name: Optional[str] = None
    new_read_write_connection_string: Optional[str] = None
    new_read_only_connection_string: Optional[str] = None


@dataclass(frozen=True)
class GPhotosConfig:
    '''
    A data class that encapsulates a Google Photos account.

    Attributes:
        id (ObjectId): The ID of this account.
        name (str): The name of the account.
        read_write_credentials (Credentials): The credentials to the account,
            with read-write permissions
        read_only_credentials (Credentials): The credentials to the account,
            with read-only access.
    '''

    id: ObjectId
    name: str
    read_write_credentials: Credentials
    read_only_credentials: Credentials


@dataclass(frozen=True)
class AddGPhotosConfigRequest:
    '''
    A data class that represents a request to add a new GPhotos configuration.

    Attributes:
        name (str): The name of the account.
        read_write_credentials (Credentials): The credentials to the account,
            with read-write permissions
        read_only_credentials (Credentials): The credentials to the account,
            with read-only access.
    '''

    name: str
    read_write_credentials: Credentials
    read_only_credentials: Credentials


@dataclass(frozen=True)
class UpdateGPhotosConfigRequest:
    '''
    A data class that represents a request to update an existing GPhotos configuration.

    Attributes:
        id (ObjectId): The ID of the object.
        new_name (Optional[str]): The new name of the account, if present.
        new_read_write_credentials (Optional[Credentials): The new credentials to the
            account, with read-write permissions, if present.
        new_read_only_credentials (Optional[Credentials]): The new credentials to the
            account, with read-only access, if present.
    '''

    id: ObjectId
    new_name: Optional[str] = None
    new_read_write_credentials: Optional[Credentials] = None
    new_read_only_credentials: Optional[Credentials] = None


@dataclass(frozen=True)
class VectorStoreConfig:
    '''
    A data class that represents a vector store config

    Attributes:
        id (ObjectId): A unique ID representing this vector store.
        name (str): A name for this vector store
    '''

    id: ObjectId
    name: str


@dataclass(frozen=True)
class MongoDbVectorStoreConfig(VectorStoreConfig):
    '''
    A data class that represents a MongoDB Vector Store config

    Attributes:
        read_write_connection_string (str): The connection string to the account,
            with read-write permissions
        read_only_connection_string (str): The connection string to the account,
            with read-only access.
    '''

    read_write_connection_string: str
    read_only_connection_string: str


@dataclass(frozen=True)
class AddVectorStoreConfigRequest:
    '''
    A data class that represents a request to add a Vector Store config
    '''

    name: str


@dataclass(frozen=True)
class AddMongoDbVectorStoreConfigRequest(AddVectorStoreConfigRequest):
    '''
    A data class that represents a MongoDB Vector Store config

    Attributes:
        read_write_connection_string (str): The connection string to the account,
            with read-write permissions
        read_only_connection_string (str): The connection string to the account,
            with read-only access.
    '''

    read_write_connection_string: str
    read_only_connection_string: str


@dataclass(frozen=True)
class UpdateVectorStoreConfigRequest:
    '''
    A data class that represents the request to update an existing vector store config.

    Attributes:
        id (ObjectId): The ID of the vector store config
    '''

    id: ObjectId


@dataclass(frozen=True)
class UpdateMongoDbVectorStoreConfigRequest(UpdateVectorStoreConfigRequest):
    '''
    A data class that represents a request to update an existing MongoDB configuration.

    Attributes:
        new_name (Optional[str]): The new name of the account, if present.
        new_read_write_connection_string (Optional[str]): The new connection string to
            the MongoDB instance with read-write permissions, if present.
        new_read_connection_string (Optional[str]): The new connection string to the
            MongoDB instance with only read permissions, if present.
    '''

    new_name: Optional[str] = None
    new_read_write_connection_string: Optional[str] = None
    new_read_only_connection_string: Optional[str] = None


class Config(ABC):
    @abstractmethod
    def get_mongodb_configs(self) -> list[MongoDbConfig]:
        '''
        Returns a list of MongoDB configurations.
        '''

    @abstractmethod
    def add_mongodb_config(self, request: AddMongoDbConfigRequest) -> MongoDbConfig:
        '''
        Adds a new MongoDB config to the config.

        Args:
            request (AddMongoDbConfigRequest): A request to add a new MongoDB config.

        Returns:
            MongoDbConfig: A new config with an assigned ID.
        '''

    @abstractmethod
    def update_mongodb_config(self, request: UpdateMongoDbConfigRequest):
        '''
        Updates an existing MongoDB config with new fields.

        Args:
            request (UpdateMongoDbConfigRequest): The details to update an exsiting
                MongoDB config.
        '''

    @abstractmethod
    def get_gphotos_configs(self) -> list[GPhotosConfig]:
        '''
        Returns a list of Google Photo configs.
        '''

    @abstractmethod
    def add_gphotos_config(self, request: AddGPhotosConfigRequest) -> GPhotosConfig:
        '''
        Adds a new Google Photos config to the config.

        Args:
            request (AddGPhotosConfigRequest): A request to add a new GPhotos config.

        Returns:
            GPhotosConfig: A new config with an assigned ID.
        '''

    @abstractmethod
    def update_gphotos_config(self, request: UpdateGPhotosConfigRequest):
        '''
        Updates an existing Google Photos config with new fields.

        Args:
            request (UpdateGPhotosConfigRequest): A request to update an existing
                GPhotos config.
        '''

    @abstractmethod
    def get_vector_store_configs(self) -> list[VectorStoreConfig]:
        '''
        Returns a list of all vector store configs in the config.

        Returns:
            list[VectorStoreConfig]: A list of all vector store configs.
        '''

    @abstractmethod
    def add_vector_store_config(
        self, request: AddVectorStoreConfigRequest
    ) -> VectorStoreConfig:
        '''
        Adds a vector store config to the config

        Args:
            request (AddVectorStoreConfigRequest): The request to add a vector store
                to the config.

        Returns:
            VectorStoreConfig: A new vector store config with an assigned ID.
        '''

    @abstractmethod
    def update_vector_store_config(self, request: UpdateVectorStoreConfigRequest):
        '''
        Updates an existing vector store config in the configs

        Args:
            request (UpdateVectorStoreConfigRequest): The request to update an vector
                store in the config
        '''

    @abstractmethod
    def get_root_album_id(self) -> AlbumId:
        """
        Gets the ID of the root album.

        Raises:
            ValueError: If there is no root album ID.

        Returns:
            AlbumId: The album ID.
        """

    @abstractmethod
    def set_root_album_id(self, album_id: AlbumId):
        """
        Sets the ID of the root album.

        Args:
            album_id (AlbumId): The album ID of the root album.
        """
