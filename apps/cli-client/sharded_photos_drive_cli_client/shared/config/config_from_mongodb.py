from typing import Mapping, cast, override

from google.oauth2.credentials import Credentials
from pymongo.mongo_client import MongoClient
from google.auth.transport.requests import AuthorizedSession
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId

from .config import Config
from ..mongodb.albums import AlbumId
from ..gphotos.client import GPhotosClientV2


class ConfigFromMongoDb(Config):
    """Represents the config stored in MongoDB"""

    def __init__(self, mongodb_client: MongoClient):
        """
        Constructs the ConfigFromMongoDbRepository

        Args:
            mongodb_client (MongoClient): The MongoDB client used to access the config
              database
        """
        self.__cached_root_album_id: AlbumId | None = None
        self.__mongodb_client = mongodb_client
        self.__mongodb_client["sharded_google_photos"].command("ping")

    @override
    def get_mongo_db_clients(self) -> list[tuple[ObjectId, MongoClient]]:
        """
        Returns a list of MongoDB clients with their IDs.
        """
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
        """
        Adds the MongoDB client to the config by its connection string.
        It will return the ID of the mongodb client.

        Args:
            name (str): The name of the MongoDB client.
            connection_string (str): The MongoDB connection string.

        Returns:
            str: The ID of the new Mongo DB client.
        """
        collection = self.__mongodb_client["sharded_google_photos"]["mongodb_clients"]
        result = collection.insert_one(
            {
                "name": name,
                "connection_string": connection_string,
            }
        )
        return result.inserted_id

    @override
    def get_gphotos_clients(self) -> list[tuple[ObjectId, GPhotosClientV2]]:
        """
        Returns a list of tuples, where each tuple is a Google Photo client ID and a
        Google Photos client instance.
        """
        collection = self.__mongodb_client["sharded_google_photos"]["gphotos_clients"]

        clients = []
        for document in collection.find({}):
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

            clients.append((document["_id"], gphotos_client))

        return clients

    @override
    def add_gphotos_client(self, gphotos_client: GPhotosClientV2) -> str:
        """
        Adds a Google Photos client to the config.

        Args:
            gphotos_client (GPhotosClientV2): The Google Photos client

        Returns:
            str: The ID of the Google Photos client.
        """
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
    def get_root_album_id(self) -> AlbumId:
        """
        Gets the ID of the root album.

        Raises:
            ValueError: If there is no root album ID.

        Returns:
            AlbumId: The album ID if it exists; else None.
        """
        doc = self.__mongodb_client["sharded_google_photos"]["root_album"].find_one({})

        if doc is None:
            raise ValueError("No root album ID!")

        return AlbumId(doc["client_id"], doc["object_id"])

    @override
    def set_root_album_id(self, album_id: AlbumId):
        """
        Sets the ID of the root album.

        Args:
            album_id (AlbumId): The album ID of the root album.
        """
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
