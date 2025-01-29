from typing import Dict, override
from bson.objectid import ObjectId

from ..mongodb.albums import AlbumId
from .config import (
    AddGPhotosConfigRequest,
    AddMongoDbConfigRequest,
    Config,
    GPhotosConfig,
    MongoDbConfig,
    UpdateGPhotosConfigRequest,
    UpdateMongoDbConfigRequest,
)


class InMemoryConfig(Config):
    """Represents the config repository stored in memory."""

    def __init__(self):
        self.__id_to_mongodb_config: Dict[ObjectId, MongoDbConfig] = {}
        self.__id_to_gphotos_config: Dict[ObjectId, GPhotosConfig] = {}
        self.__root_album_id = None

    @override
    def get_mongodb_configs(self) -> list[MongoDbConfig]:
        return [item for (_, item) in self.__id_to_mongodb_config.items()]

    @override
    def add_mongodb_config(self, request: AddMongoDbConfigRequest) -> MongoDbConfig:
        new_id = self.__generate_unique_object_id()
        config = MongoDbConfig(
            id=new_id,
            name=request.name,
            read_write_connection_string=request.read_write_connection_string,
            read_only_connection_string=request.read_only_connection_string,
        )
        self.__id_to_mongodb_config[new_id] = config
        return config

    @override
    def update_mongodb_config(self, request: UpdateMongoDbConfigRequest):
        if request.id not in self.__id_to_mongodb_config:
            raise ValueError(f"Mongo Config ID {request.id} does not exist")

        old_config = self.__id_to_mongodb_config[request.id]
        new_config = MongoDbConfig(
            id=old_config.id,
            name=request.new_name if request.new_name else old_config.name,
            read_write_connection_string=(
                request.new_read_write_connection_string
                if request.new_read_write_connection_string
                else old_config.read_write_connection_string
            ),
            read_only_connection_string=(
                request.new_read_only_connection_string
                if request.new_read_only_connection_string
                else old_config.read_only_connection_string
            ),
        )

        self.__id_to_mongodb_config[request.id] = new_config

    @override
    def get_gphotos_configs(self) -> list[GPhotosConfig]:
        return [item for _, item in self.__id_to_gphotos_config.items()]

    @override
    def add_gphotos_config(self, request: AddGPhotosConfigRequest) -> GPhotosConfig:
        new_id = self.__generate_unique_object_id()
        config = GPhotosConfig(
            id=new_id,
            name=request.name,
            read_write_credentials=request.read_write_credentials,
            read_only_credentials=request.read_only_credentials,
        )
        self.__id_to_gphotos_config[new_id] = config
        return config

    @override
    def update_gphotos_config(self, request: UpdateGPhotosConfigRequest):
        if request.id not in self.__id_to_gphotos_config:
            raise ValueError(f"GPhotos Config ID {request.id} does not exist")

        old_config = self.__id_to_gphotos_config[request.id]
        new_config = GPhotosConfig(
            id=old_config.id,
            name=request.new_name if request.new_name else old_config.name,
            read_write_credentials=(
                request.new_read_write_credentials
                if request.new_read_write_credentials
                else old_config.read_write_credentials
            ),
            read_only_credentials=(
                request.new_read_only_credentials
                if request.new_read_only_credentials
                else old_config.read_only_credentials
            ),
        )

        self.__id_to_gphotos_config[request.id] = new_config

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
        while id in self.__id_to_gphotos_config or id in self.__id_to_mongodb_config:
            id = ObjectId()

        return id
