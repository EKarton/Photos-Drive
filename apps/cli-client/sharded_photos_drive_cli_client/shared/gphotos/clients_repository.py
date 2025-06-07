import logging
from typing import Dict, Optional
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from bson.objectid import ObjectId

from .client import GPhotosClientV2, ListenableCredentials, TokenRefreshCallback
from ..config.config import Config, GPhotosConfig, UpdateGPhotosConfigRequest

logger = logging.getLogger(__name__)


class TokenCallback(TokenRefreshCallback):
    def __init__(self, config_repo: Config, config: GPhotosConfig, creds: Credentials):
        self._config_repo = config_repo
        self._config = config
        self._creds = creds

    def before_refresh(self) -> None:
        pass

    def after_refresh(self, error: Optional[Exception]) -> None:
        if not error:
            logger.debug(f"Updated gphotos credentials for {self._config.id}")
            self._config_repo.update_gphotos_config(
                UpdateGPhotosConfigRequest(
                    id=self._config.id,
                    new_read_write_credentials=self._creds,
                )
            )
        else:
            logger.error(f"Error while updating gphotos credentials: {error}")


class GPhotosClientsRepository:
    def __init__(self) -> None:
        self.__id_to_client: Dict[ObjectId, GPhotosClientV2] = {}

    @staticmethod
    def build_from_config(
        config_repo: Config,
    ) -> "GPhotosClientsRepository":
        """
        A factory method that builds the GPhotosClientsRepository from the Config.

        Args:
            config_repo (Config): The config repository

        Returns:
            GPhotosClientsRepository: An instance of the GPhotos clients repo.
        """
        gphotos_clients_repo = GPhotosClientsRepository()

        for gphotos_config in config_repo.get_gphotos_configs():
            listenable_credentials = ListenableCredentials(
                token=gphotos_config.read_write_credentials.token,
                refresh_token=gphotos_config.read_write_credentials.refresh_token,
                token_uri=gphotos_config.read_write_credentials.token_uri,
                client_id=gphotos_config.read_write_credentials.client_id,
                client_secret=gphotos_config.read_write_credentials.client_secret,
            )

            gphotos_client = GPhotosClientV2(
                name=gphotos_config.name,
                session=AuthorizedSession(listenable_credentials),
            )

            listenable_credentials.set_token_refresh_callback(
                TokenCallback(config_repo, gphotos_config, listenable_credentials)
            )

            gphotos_clients_repo.add_gphotos_client(gphotos_config.id, gphotos_client)

        return gphotos_clients_repo

    def add_gphotos_client(self, id: ObjectId, client: GPhotosClientV2):
        """
        Adds a GPhotos client to the repository.

        Args:
            id (ObjectId): The ID of the client.
            client (GPhotosClientV2): The GPhotos client.

        Raises:
            ValueError: If ID already exists.
        """
        if id in self.__id_to_client:
            raise ValueError(f"GPhotos Client ID {str(id)} already exists")

        self.__id_to_client[id] = client

    def get_client_by_id(self, id: ObjectId) -> GPhotosClientV2:
        """
        Gets a Google Photos client from the repository.

        Args:
            id (ObjectId): The ID of the client.

        Raises:
            ValueError: If ID does not exist.
        """
        if id not in self.__id_to_client:
            raise ValueError(f"Cannot find Google Photos client {str(id)}")
        return self.__id_to_client[id]

    def get_all_clients(self) -> list[tuple[ObjectId, GPhotosClientV2]]:
        """
        Returns all Google Photos client from the repository.

        Returns:
            ist[(ObjectId, GPhotosClientV2)]: A list of clients with their ids
        """
        return [(id, client) for id, client in self.__id_to_client.items()]
