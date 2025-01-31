import logging
from typing import Dict
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from bson.objectid import ObjectId

from .client import GPhotosClientV2, ListenableCredentials
from ..config.config import Config, UpdateGPhotosConfigRequest

logger = logging.getLogger(__name__)


class GPhotosClientsRepository:
    def __init__(self):
        self.__id_to_client: Dict[str, GPhotosClientV2] = {}

    @staticmethod
    def build_from_config_repo(
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
                client_id=gphotos_config.read_write_credentials.client_id,
                client_secret=gphotos_config.read_write_credentials.client_secret,
            )

            gphotos_client = GPhotosClientV2(
                name=gphotos_config.name,
                session=AuthorizedSession(listenable_credentials),
            )

            def handle_token_refresh(new_creds: Credentials):
                logger.debug(f"Refreshed gphotos credentials for {gphotos_config.id}")
                config_repo.update_gphotos_config(UpdateGPhotosConfigRequest)

            listenable_credentials.set_token_refresh_callback()

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
        str_id = str(id)
        if str_id in self.__id_to_client:
            raise ValueError(f"GPhotos Client ID {id} already exists")

        self.__id_to_client[str_id] = client

    def get_client_by_id(self, id: ObjectId) -> GPhotosClientV2:
        """
        Gets a Google Photos client from the repository.

        Args:
            id (ObjectId): The ID of the client.

        Raises:
            ValueError: If ID does not exist.
        """
        str_id = str(id)
        if str_id not in self.__id_to_client:
            raise ValueError(f"Cannot find Google Photos client {id}")
        return self.__id_to_client[str_id]

    def get_all_clients(self) -> list[tuple[ObjectId, GPhotosClientV2]]:
        """
        Returns all Google Photos client from the repository.

        Returns:
            ist[(ObjectId, GPhotosClientV2)]: A list of clients with their ids
        """
        return [(ObjectId(id), client) for id, client in self.__id_to_client.items()]
