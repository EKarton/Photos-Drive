import configparser
from typing import override
from google.oauth2.credentials import Credentials
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

GPHOTOS_CONFIG_TYPE = "gphotos_config"
MONGODB_CONFIG_TYPE = "mongodb_config"
ROOT_ALBUM_TYPE = "root_album"


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
    def get_mongodb_configs(self) -> list[MongoDbConfig]:
        configs = []
        for section_id in self._config.sections():
            if self._config.get(section_id, "type") != MONGODB_CONFIG_TYPE:
                continue

            config = MongoDbConfig(
                id=ObjectId(section_id.strip()),
                name=self._config.get(section_id, "name"),
                read_write_connection_string=self._config.get(
                    section_id, "read_write_connection_string"
                ),
                read_only_connection_string=self._config.get(
                    section_id, "read_only_connection_string"
                ),
            )
            configs.append(config)

        return configs

    @override
    def add_mongodb_config(self, request: AddMongoDbConfigRequest) -> MongoDbConfig:
        id = self.__generate_unique_object_id()
        id_str = str(id)
        self._config.add_section(id_str)
        self._config.set(id_str, "type", MONGODB_CONFIG_TYPE)
        self._config.set(id_str, "name", request.name)
        self._config.set(
            id_str, "read_write_connection_string", request.read_write_connection_string
        )
        self._config.set(
            id_str, "read_only_connection_string", request.read_only_connection_string
        )
        self.flush()

        return MongoDbConfig(
            id=id,
            name=request.name,
            read_write_connection_string=request.read_write_connection_string,
            read_only_connection_string=request.read_only_connection_string,
        )

    @override
    def update_mongodb_config(self, request: UpdateMongoDbConfigRequest):
        id_str = str(request.id)
        if not self._config.has_section(id_str):
            raise ValueError(f"Cannot find MongoDB config {request.id}")

        if self._config.get(id_str, "type") != MONGODB_CONFIG_TYPE:
            raise ValueError(f"ID {request.id} is not a MongoDB config")

        if request.new_name:
            self._config.set(id_str, "name", request.new_name)

        if request.new_read_write_connection_string:
            self._config.set(
                id_str,
                "read_write_connection_string",
                request.new_read_write_connection_string,
            )

        if request.new_read_only_connection_string:
            self._config.set(
                id_str,
                "read_only_connection_string",
                request.new_read_only_connection_string,
            )

        self.flush()

    @override
    def get_gphotos_configs(self) -> list[GPhotosConfig]:
        configs = []
        for section_id in self._config.sections():
            if self._config.get(section_id, "type") != GPHOTOS_CONFIG_TYPE:
                continue

            config = GPhotosConfig(
                id=ObjectId(section_id.strip()),
                name=self._config.get(section_id, "name"),
                read_write_credentials=Credentials(
                    token=self._config.get(section_id, "read_write_token"),
                    refresh_token=self._config.get(
                        section_id, "read_write_refresh_token"
                    ),
                    client_id=self._config.get(section_id, "read_write_client_id"),
                    client_secret=self._config.get(
                        section_id, "read_write_client_secret"
                    ),
                    token_uri=self._config.get(section_id, "read_write_token_uri"),
                ),
                read_only_credentials=Credentials(
                    token=self._config.get(section_id, "read_only_token"),
                    refresh_token=self._config.get(
                        section_id, "read_only_refresh_token"
                    ),
                    client_id=self._config.get(section_id, "read_only_client_id"),
                    client_secret=self._config.get(
                        section_id, "read_only_client_secret"
                    ),
                    token_uri=self._config.get(section_id, "read_only_token_uri"),
                ),
            )
            configs.append(config)

        return configs

    @override
    def add_gphotos_config(self, request: AddGPhotosConfigRequest) -> GPhotosConfig:
        id = self.__generate_unique_object_id()
        id_str = str(id)

        self._config.add_section(id_str)
        self._config.set(id_str, "type", GPHOTOS_CONFIG_TYPE)
        self._config.set(id_str, "name", str(request.name))
        self.__set_read_write_credentials(id_str, request.read_write_credentials)
        self.__set_read_only_credentials(id_str, request.read_only_credentials)
        self.flush()

        return GPhotosConfig(
            id=id,
            name=request.name,
            read_write_credentials=request.read_write_credentials,
            read_only_credentials=request.read_only_credentials,
        )

    @override
    def update_gphotos_config(self, request: UpdateGPhotosConfigRequest):
        id_str = str(request.id)
        if not self._config.has_section(id_str):
            raise ValueError(f"Cannot find GPhotos config {id_str}")

        if self._config.get(id_str, "type") != GPHOTOS_CONFIG_TYPE:
            raise ValueError(f"ID {id_str} is not a GPhotos config")

        if request.new_name:
            self._config.set(id_str, "name", str(request.new_name))

        if request.new_read_write_credentials:
            self.__set_read_write_credentials(
                id_str, request.new_read_write_credentials
            )

        if request.new_read_only_credentials:
            self.__set_read_only_credentials(id_str, request.new_read_only_credentials)

        self.flush()

    def __set_read_write_credentials(self, id_str: str, creds: Credentials):
        self._config.set(id_str, "read_write_token", str(creds.token))
        self._config.set(id_str, "read_write_refresh_token", str(creds.refresh_token))
        self._config.set(id_str, "read_write_client_id", str(creds.client_id))
        self._config.set(id_str, "read_write_client_secret", str(creds.client_secret))
        self._config.set(id_str, "read_write_token_uri", str(creds.token_uri))

    def __set_read_only_credentials(self, id_str: str, creds: Credentials):
        self._config.set(id_str, "read_only_token", str(creds.token))
        self._config.set(id_str, "read_only_refresh_token", str(creds.refresh_token))
        self._config.set(id_str, "read_only_client_id", str(creds.client_id))
        self._config.set(id_str, "read_only_client_secret", str(creds.client_secret))
        self._config.set(id_str, "read_only_token_uri", str(creds.token_uri))

    @override
    def get_root_album_id(self) -> AlbumId:
        for section_id in self._config.sections():
            if self._config.get(section_id, "type") != ROOT_ALBUM_TYPE:
                continue

            return AlbumId(
                client_id=ObjectId(self._config.get(section_id, "client_id").strip()),
                object_id=ObjectId(self._config.get(section_id, "object_id").strip()),
            )

        raise ValueError("Cannot find root album")

    @override
    def set_root_album_id(self, album_id: AlbumId):
        client_id = self.__generate_unique_object_id()
        client_id_str = str(client_id)

        self._config.add_section(client_id_str)
        self._config.set(client_id_str, "type", ROOT_ALBUM_TYPE)
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
