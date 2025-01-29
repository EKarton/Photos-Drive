import logging
from typing import Mapping, cast, override
from google.oauth2.credentials import Credentials
from pymongo.mongo_client import MongoClient
from google.auth.transport.requests import AuthorizedSession
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId

from .config import (
    AddGPhotosConfigRequest,
    AddMongoDbConfigRequest,
    Config,
    GPhotosConfig,
    MongoDbConfig,
    UpdateGPhotosConfigRequest,
    UpdateMongoDbConfigRequest,
)
from ..mongodb.albums import AlbumId
from ..gphotos.client import GPhotosClientV2

logger = logging.getLogger(__name__)


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
        self.__mongodb_client["sharded_google_photos"].command("ping")

    @override
    def get_mongo_db_clients(self) -> list[tuple[ObjectId, MongoClient]]:
        collection = self.__mongodb_client["sharded_google_photos"]["mongodb_clients"]

        clients = []
        for document in collection.find({}):
            mongodb_client: MongoClient = MongoClient(
                document["connection_string"], server_api=ServerApi("1")
            )

            clients.append((document["_id"], mongodb_client))

        return clients

    @override
    def add_mongo_db_client(self, name: str, connection_string: str) -> str:
        collection = self.__mongodb_client["sharded_google_photos"]["mongodb_clients"]
        result = collection.insert_one(
            {
                "name": name,
                "connection_string": connection_string,
            }
        )
        return result.inserted_id

    @override
    def get_mongodb_configs(self) -> list[MongoDbConfig]:
        raise NotImplementedError()

    @override
    def add_mongodb_config(self, request: AddMongoDbConfigRequest) -> MongoDbConfig:
        raise NotImplementedError()

    @override
    def update_mongodb_config(self, request: UpdateMongoDbConfigRequest):
        raise NotADirectoryError()

    @override
    def get_gphotos_clients(self) -> list[tuple[ObjectId, GPhotosClientV2]]:
        collection = self.__mongodb_client["sharded_google_photos"]["gphotos_clients"]

        clients = []
        for document in collection.find({}):
            client_id = document["_id"]
            creds = Credentials(
                token=document["token"],
                refresh_token=document["refresh_token"],
                token_uri=document["token_uri"],
                client_id=document["client_id"],
                client_secret=document["client_secret"],
            )
            gphotos_client = GPhotosClientV2(
                name=document["name"], session=AuthorizedSession(creds)
            )

            clients.append((client_id, gphotos_client))

        return clients

    @override
    def add_gphotos_client(self, gphotos_client: GPhotosClientV2) -> str:
        credentials = cast(Credentials, gphotos_client.session().credentials)

        collection = self.__mongodb_client["sharded_google_photos"]["gphotos_clients"]
        result = collection.insert_one(
            {
                "name": gphotos_client.name(),
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
            }
        )
        return result.inserted_id

    @override
    def get_gphotos_configs(self) -> list[GPhotosConfig]:
        raise NotImplementedError()

    @override
    def add_gphotos_config(self, request: AddGPhotosConfigRequest) -> GPhotosConfig:
        raise NotImplementedError()

    @override
    def update_gphotos_config(self, request: UpdateGPhotosConfigRequest):
        raise NotImplementedError()

    @override
    def get_root_album_id(self) -> AlbumId:
        doc = self.__mongodb_client["sharded_google_photos"]["root_album"].find_one({})

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
        self.__mongodb_client["sharded_google_photos"]["root_album"].update_one(
            filter=filter_query, update=set_query, upsert=True
        )
