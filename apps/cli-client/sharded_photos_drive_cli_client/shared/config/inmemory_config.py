from typing import Dict, override

from mongomock import MongoClient
from bson.objectid import ObjectId


from .config import Config
from ..gphotos.client import GPhotosClientV2
from ..mongodb.albums import AlbumId


class InMemoryConfig(Config):
    """Represents the config repository stored in memory."""

    def __init__(self):
        self.__id_to_mongodb_clients: Dict[str, MongoClient] = {}
        self.__id_to_gphotos_clients: Dict[str, GPhotosClientV2] = {}
        self.__root_album_id = None

    @override
    def get_mongo_db_clients(self) -> list[tuple[ObjectId, MongoClient]]:
        return [
            (ObjectId(id), client)
            for id, client in self.__id_to_mongodb_clients.items()
        ]

    @override
    def add_mongo_db_client(self, mongodb_client: MongoClient) -> str:  # type: ignore
        client_id = self.__generate_unique_object_id()
        client_id_str = str(client_id)
        self.__id_to_mongodb_clients[client_id_str] = mongodb_client

        return client_id_str

    @override
    def get_gphotos_clients(self) -> list[tuple[ObjectId, GPhotosClientV2]]:
        return [
            (ObjectId(id), client)
            for id, client in self.__id_to_gphotos_clients.items()
        ]

    @override
    def add_gphotos_client(self, gphotos_client: GPhotosClientV2) -> str:
        client_id = self.__generate_unique_object_id()
        client_id_str = str(client_id)

        self.__id_to_gphotos_clients[client_id_str] = gphotos_client

        return client_id_str

    @override
    def get_root_album_id(self) -> AlbumId:
        if self.__root_album_id:
            return self.__root_album_id

        raise ValueError("Cannot find root album")

    @override
    def set_root_album_id(self, album_id: AlbumId):
        self.__root_album_id = album_id

    def __generate_unique_object_id(self) -> ObjectId:
        id = ObjectId()
        str_id = str(id)
        while (
            str_id in self.__id_to_gphotos_clients
            or str_id in self.__id_to_mongodb_clients
        ):
            id = ObjectId()
            str_id = str(id)

        return id
