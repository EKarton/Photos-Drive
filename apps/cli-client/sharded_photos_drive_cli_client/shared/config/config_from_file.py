import configparser
from typing import cast, override

from google.oauth2.credentials import Credentials
from pymongo.mongo_client import MongoClient
from google.auth.transport.requests import AuthorizedSession
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId


from .config import Config
from ..gphotos.client import GPhotosClientV2
from ..mongodb.albums import AlbumId


class ConfigFromFile(Config):
    """Represents the config repository stored in a config file."""

    def __init__(self, config_file_path: str):
        """
        Constructs the ConfigFromFileRepository

        Args:
            config_file_path (str): The file path to the config file
        """
        self._config_file_path = config_file_path
        self._config = configparser.ConfigParser()
        self._config.read(config_file_path)

    @override
    def get_mongo_db_clients(self) -> list[tuple[ObjectId, MongoClient]]:
        """
        Returns a list of MongoDB clients with their IDs.
        """
        results = []
        for section_id in self._config.sections():
            if self._config.get(section_id, "type") != "mongodb":
                continue

            mongodb_client: MongoClient = MongoClient(
                self._config.get(section_id, "connection_string"),
                server_api=ServerApi("1"),
            )
            results.append(
                (
                    ObjectId(section_id.strip()),
                    mongodb_client,
                )
            )

        return results

    @override
    def add_mongo_db_client(self, name: str, connection_string: str) -> str:
        """
        Adds the MongoDB client to the config by its connection string.
        It will return the ID of the mongodb client.

        Args:
            name (str): The name of the MongoDB client.
            connection_string (str): The MongoDB connection string.

        Raises:
            ValueError: If ID already exists.

        Returns:
            str: The ID of the new Mongo DB client.
        """
        client_id = self.__generate_unique_object_id()
        client_id_str = str(client_id)

        self._config.add_section(client_id_str)
        self._config.set(client_id_str, "type", "mongodb")
        self._config.set(client_id_str, "name", name)
        self._config.set(client_id_str, "connection_string", connection_string)
        self.flush()

        return name

    @override
    def get_gphotos_clients(self) -> list[tuple[ObjectId, GPhotosClientV2]]:
        """
        Returns a list of tuples, where each tuple is a Google Photo client ID and a
        Google Photos client instance.
        """
        results = []
        for section_id in self._config.sections():
            if self._config.get(section_id, "type") != "gphotos":
                continue

            creds = Credentials(
                token=self._config.get(section_id, "token"),
                refresh_token=self._config.get(section_id, "refresh_token"),
                client_id=self._config.get(section_id, "client_id"),
                client_secret=self._config.get(section_id, "client_secret"),
                token_uri=self._config.get(section_id, "token_uri"),
            )
            gphotos_client: GPhotosClientV2 = GPhotosClientV2(
                name=self._config.get(section_id, "name"),
                session=AuthorizedSession(creds),
            )
            results.append((ObjectId(section_id.strip()), gphotos_client))

        return results

    @override
    def add_gphotos_client(self, gphotos_client: GPhotosClientV2) -> str:
        """
        Adds a Google Photos client to the config.

        Args:
            gphotos_client (GPhotosClientV2): The Google Photos client

        Returns:
            str: The ID of the Google Photos client.
        """
        client_id = self.__generate_unique_object_id()
        client_id_str = str(client_id)
        name = gphotos_client.name()

        self._config.add_section(client_id_str)
        self._config.set(client_id_str, "type", "gphotos")
        self._config.set(client_id_str, "name", name)
        credentials = cast(Credentials, gphotos_client.session().credentials)

        if credentials.refresh_token:
            self._config.set(client_id_str, "refresh_token", credentials.refresh_token)

        if credentials.token:
            self._config.set(client_id_str, "token", credentials.token)

        if credentials.client_id:
            self._config.set(client_id_str, "client_id", credentials.client_id)

        if credentials.client_secret:
            self._config.set(client_id_str, "client_secret", credentials.client_secret)

        if credentials.token_uri:
            self._config.set(client_id_str, "token_uri", credentials.token_uri)

        self.flush()

        return name

    @override
    def get_root_album_id(self) -> AlbumId:
        """
        Gets the ID of the root album.

        Raises:
            ValueError: If there is no root album ID.

        Returns:
            AlbumId: The album ID if it exists; else None.
        """
        for section_id in self._config.sections():
            if self._config.get(section_id, "type") != "root_album":
                continue

            return AlbumId(
                client_id=ObjectId(self._config.get(section_id, "client_id").strip()),
                object_id=ObjectId(self._config.get(section_id, "object_id").strip()),
            )

        raise ValueError("Cannot find root album")

    @override
    def set_root_album_id(self, album_id: AlbumId):
        """
        Sets the ID of the root album.

        Args:
            album_id (AlbumId): The album ID of the root album.
        """
        client_id = self.__generate_unique_object_id()
        client_id_str = str(client_id)

        self._config.add_section(client_id_str)
        self._config.set(client_id_str, "type", "root_album")
        self._config.set(client_id_str, "client_id", str(album_id.client_id))
        self._config.set(client_id_str, "object_id", str(album_id.object_id))
        self.flush()

    def flush(self):
        """
        Writes the config back to the file.
        """
        with open(self._config_file_path, "w") as config_file:
            self._config.write(config_file)

    def __generate_unique_object_id(self) -> ObjectId:
        id = ObjectId()
        while self._config.has_section(str(id)):
            id = ObjectId()

        return id
