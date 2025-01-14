from abc import ABC, abstractmethod

from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId

from ..gphotos.client import GPhotosClientV2
from ..mongodb.albums import AlbumId


class Config(ABC):
    @abstractmethod
    def get_mongo_db_clients(self) -> list[tuple[ObjectId, MongoClient]]:
        """
        Returns a list of MongoDB clients with their IDs.
        """

    @abstractmethod
    def add_mongo_db_client(self, name: str, connection_string: str) -> str:
        """
        Adds the MongoDB client to the config by its connection string.
        It will return the ID of the mongodb client.

        Args:
            name (str): The name of the MongoDB client.
            connection_string (str): The MongoDB connection string.

        Returns:
            str: The ID of the new Mongo DB client.
        """

    @abstractmethod
    def get_gphotos_clients(self) -> list[tuple[ObjectId, GPhotosClientV2]]:
        """
        Returns a list of tuples, where each tuple is a Google Photo client ID and a
        Google Photos client instance.
        """

    @abstractmethod
    def add_gphotos_client(self, gphotos_client: GPhotosClientV2) -> str:
        """
        Adds a Google Photos client to the config.

        Args:
            gphotos_client (GPhotosClientV2): The Google Photos client

        Returns:
            str: The ID of the Google Photos client.
        """

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
