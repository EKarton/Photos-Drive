import logging
from typing import Any, Dict, Mapping, cast

from bson.objectid import ObjectId
from google.oauth2.credentials import Credentials
from pymongo.mongo_client import MongoClient
from typing_extensions import override

from photos_drive.shared.config.config import (
    AddGPhotosConfigRequest,
    AddMongoDbConfigRequest,
    AddMongoDbVectorStoreConfigRequest,
    AddVectorStoreConfigRequest,
    Config,
    GPhotosConfig,
    MongoDbConfig,
    MongoDbVectorStoreConfig,
    UpdateGPhotosConfigRequest,
    UpdateMongoDbConfigRequest,
    UpdateMongoDbVectorStoreConfigRequest,
    UpdateVectorStoreConfigRequest,
    VectorStoreConfig,
)
from photos_drive.shared.metadata.album_id import AlbumId

logger = logging.getLogger(__name__)

MONGODB_VECTOR_STORE_TYPE = 'mongodb-vector-store-type'


class ConfigFromMongoDb(Config):
    """Represents the config stored in MongoDB"""

    def __init__(self, mongodb_client: MongoClient):
        """
        Constructs the ConfigFromMongoDbRepository

        Args:
            mongodb_client (MongoClient): The MongoDB client used to access the config
              database
        """
        self.__mongodb_client = mongodb_client
        self.__vector_store_collection = mongodb_client["photos_drive"][
            "vector_store_configs"
        ]

    @override
    def get_mongodb_configs(self) -> list[MongoDbConfig]:
        collection = self.__mongodb_client["photos_drive"]["mongodb_configs"]
        configs = []
        for document in collection.find({}):
            config = MongoDbConfig(
                id=document["_id"],
                name=document['name'],
                read_write_connection_string=document['read_write_connection_string'],
                read_only_connection_string=document['read_only_connection_string'],
            )
            configs.append(config)

        return configs

    @override
    def add_mongodb_config(self, request: AddMongoDbConfigRequest) -> MongoDbConfig:
        collection = self.__mongodb_client["photos_drive"]["mongodb_configs"]
        result = collection.insert_one(
            {
                "name": request.name,
                "read_write_connection_string": request.read_write_connection_string,
                "read_only_connection_string": request.read_only_connection_string,
            }
        )

        return MongoDbConfig(
            id=cast(ObjectId, result.inserted_id),
            name=request.name,
            read_write_connection_string=request.read_write_connection_string,
            read_only_connection_string=request.read_only_connection_string,
        )

    @override
    def update_mongodb_config(self, request: UpdateMongoDbConfigRequest):
        filter_query: Mapping = {"_id": request.id}
        set_query: Mapping = {"$set": {}}

        if request.new_name:
            set_query["$set"]['name'] = request.new_name

        if request.new_read_write_connection_string:
            set_query["$set"][
                'read_write_connection_string'
            ] = request.new_read_write_connection_string

        if request.new_read_only_connection_string:
            set_query["$set"][
                'read_only_connection_string'
            ] = request.new_read_only_connection_string

        collection = self.__mongodb_client["photos_drive"]["mongodb_configs"]
        result = collection.update_one(
            filter=filter_query, update=set_query, upsert=False
        )

        if result.matched_count != 1:
            raise ValueError(f"Unable to update MongoDB config {request.id}")

    @override
    def get_gphotos_configs(self) -> list[GPhotosConfig]:
        collection = self.__mongodb_client["photos_drive"]["gphotos_configs"]
        configs = []
        for document in collection.find({}):
            id = document["_id"]
            name = document["name"]
            read_write_credentials = Credentials(
                token=document["read_write_credentials"]["token"],
                refresh_token=document["read_write_credentials"]["refresh_token"],
                token_uri=document["read_write_credentials"]["token_uri"],
                client_id=document["read_write_credentials"]["client_id"],
                client_secret=document["read_write_credentials"]["client_secret"],
            )

            read_only_credentials = Credentials(
                token=document["read_only_credentials"]["token"],
                refresh_token=document["read_only_credentials"]["refresh_token"],
                token_uri=document["read_only_credentials"]["token_uri"],
                client_id=document["read_only_credentials"]["client_id"],
                client_secret=document["read_only_credentials"]["client_secret"],
            )

            configs.append(
                GPhotosConfig(id, name, read_write_credentials, read_only_credentials)
            )

        return configs

    @override
    def add_gphotos_config(self, request: AddGPhotosConfigRequest) -> GPhotosConfig:
        collection = self.__mongodb_client["photos_drive"]["gphotos_configs"]
        result = collection.insert_one(
            {
                "name": request.name,
                "read_write_credentials": {
                    "token": request.read_write_credentials.token,
                    "refresh_token": request.read_write_credentials.refresh_token,
                    "token_uri": request.read_write_credentials.token_uri,
                    "client_id": request.read_write_credentials.client_id,
                    "client_secret": request.read_write_credentials.client_secret,
                },
                "read_only_credentials": {
                    "token": request.read_only_credentials.token,
                    "refresh_token": request.read_only_credentials.refresh_token,
                    "token_uri": request.read_only_credentials.token_uri,
                    "client_id": request.read_only_credentials.client_id,
                    "client_secret": request.read_only_credentials.client_secret,
                },
            }
        )

        return GPhotosConfig(
            id=cast(ObjectId, result.inserted_id),
            name=request.name,
            read_write_credentials=request.read_write_credentials,
            read_only_credentials=request.read_only_credentials,
        )

    @override
    def update_gphotos_config(self, request: UpdateGPhotosConfigRequest):
        filter_query: Mapping = {"_id": request.id}
        set_query: Mapping = {"$set": {}}

        if request.new_name:
            set_query["$set"]['name'] = request.new_name

        if request.new_read_write_credentials:
            set_query["$set"]['read_write_credentials'] = {
                "token": request.new_read_write_credentials.token,
                "refresh_token": request.new_read_write_credentials.refresh_token,
                "token_uri": request.new_read_write_credentials.token_uri,
                "client_id": request.new_read_write_credentials.client_id,
                "client_secret": request.new_read_write_credentials.client_secret,
            }

        if request.new_read_only_credentials:
            set_query["$set"]['read_only_credentials'] = {
                "token": request.new_read_only_credentials.token,
                "refresh_token": request.new_read_only_credentials.refresh_token,
                "token_uri": request.new_read_only_credentials.token_uri,
                "client_id": request.new_read_only_credentials.client_id,
                "client_secret": request.new_read_only_credentials.client_secret,
            }

        collection = self.__mongodb_client["photos_drive"]["gphotos_configs"]
        result = collection.update_one(
            filter=filter_query, update=set_query, upsert=False
        )

        if result.matched_count != 1:
            raise ValueError(f"Cannot find GPhotos config {request.id}")

    @override
    def get_root_album_id(self) -> AlbumId:
        doc = self.__mongodb_client["photos_drive"]["root_album"].find_one({})

        if doc is None:
            raise ValueError("No root album ID!")

        return AlbumId(doc["client_id"], doc["object_id"])

    @override
    def set_root_album_id(self, album_id: AlbumId):
        filter_query: Mapping = {}
        set_query: Mapping = {
            "$set": {
                "client_id": album_id.client_id,
                "object_id": album_id.object_id,
            }
        }
        self.__mongodb_client["photos_drive"]["root_album"].update_one(
            filter=filter_query, update=set_query, upsert=True
        )

    @override
    def get_vector_store_configs(self) -> list[VectorStoreConfig]:
        configs: list[VectorStoreConfig] = []
        for doc in self.__vector_store_collection.find({}):
            if doc['type'] == MONGODB_VECTOR_STORE_TYPE:
                configs.append(self.__parse_mongodb_vector_store_config(doc))
        return configs

    def __parse_mongodb_vector_store_config(
        self, doc: Dict[str, Any]
    ) -> MongoDbVectorStoreConfig:
        return MongoDbVectorStoreConfig(
            id=doc["_id"],
            name=doc['name'],
            read_write_connection_string=doc['read_write_connection_string'],
            read_only_connection_string=doc['read_only_connection_string'],
        )

    @override
    def add_vector_store_config(
        self, request: AddVectorStoreConfigRequest
    ) -> VectorStoreConfig:
        if isinstance(request, AddMongoDbVectorStoreConfigRequest):
            return self.__add_mongodb_vector_store_config(request)
        else:
            raise NotImplementedError(
                f'Adding vector store config {type(request)} not supported'
            )

    def __add_mongodb_vector_store_config(
        self, request: AddMongoDbVectorStoreConfigRequest
    ) -> MongoDbVectorStoreConfig:
        result = self.__vector_store_collection.insert_one(
            {
                "name": request.name,
                "type": MONGODB_VECTOR_STORE_TYPE,
                "read_write_connection_string": request.read_write_connection_string,
                "read_only_connection_string": request.read_only_connection_string,
            }
        )

        return MongoDbVectorStoreConfig(
            id=cast(ObjectId, result.inserted_id),
            name=request.name,
            read_write_connection_string=request.read_write_connection_string,
            read_only_connection_string=request.read_only_connection_string,
        )

    @override
    def update_vector_store_config(self, request: UpdateVectorStoreConfigRequest):
        if isinstance(request, UpdateMongoDbVectorStoreConfigRequest):
            self.__update_mongodb_vector_store_config(request)
        else:
            raise NotImplementedError(
                f'Updating vector store config {type(request)} not supported'
            )

    def __update_mongodb_vector_store_config(
        self, request: UpdateMongoDbVectorStoreConfigRequest
    ):
        filter_query: Mapping = {"_id": request.id}
        set_query: Mapping = {"$set": {}}

        if request.new_name:
            set_query["$set"]['name'] = request.new_name

        if request.new_read_write_connection_string:
            set_query["$set"][
                'read_write_connection_string'
            ] = request.new_read_write_connection_string

        if request.new_read_only_connection_string:
            set_query["$set"][
                'read_only_connection_string'
            ] = request.new_read_only_connection_string

        result = self.__vector_store_collection.update_one(
            filter=filter_query, update=set_query, upsert=False
        )

        if result.matched_count != 1:
            raise ValueError(
                f"Unable to update MongoDB Vector Store config {request.id}"
            )
