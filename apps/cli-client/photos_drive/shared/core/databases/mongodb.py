from abc import ABC, abstractmethod
import logging
from typing import Dict, override

from bson.objectid import ObjectId
from pymongo.client_session import ClientSession
from pymongo.mongo_client import MongoClient
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

from photos_drive.shared.core.config.config import Config
from photos_drive.shared.core.databases.transactions import (
    TransactionsManager,
)

logger = logging.getLogger(__name__)


class MongoDBSessionsProvider(ABC):
    '''
    This class is a provider to fetch MongoDB sessions for a particular MongoDB client.
    '''

    @abstractmethod
    def get_session_for_client_id(self, client_id: ObjectId) -> ClientSession | None:
        """
        Returns the MongoDB session for a ClientID.

        Args:
            client_id (ObjectId): The ID of the MongoDB client

        Returns:
            ClientSession | None: The session if it has already started; else None.
        """
        pass


class MongoDBClientsRepository(MongoDBSessionsProvider, TransactionsManager):
    '''
    This class is a repository for MongoDB clients and its sessions.
    '''

    def __init__(self) -> None:
        self.__id_to_client: Dict[str, MongoClient] = {}
        self.__client_id_to_session: dict[ObjectId, ClientSession] = {}
        self.__transaction_in_progress = False

    @staticmethod
    def build_from_config(
        config: Config,
    ) -> "MongoDBClientsRepository":
        """
        A factory method that builds the MongoDBClientsRepository from the config.

        Args:
            config (Config): The config

        Returns:
            MongoDBClientsRepository: An instance of the Mongo DB clients repo.
        """
        mongodb_clients_repo = MongoDBClientsRepository()

        for mongodb_config in config.get_mongodb_configs():
            mongodb_client: MongoClient = MongoClient(
                mongodb_config.read_write_connection_string
            )

            mongodb_clients_repo.add_mongodb_client(mongodb_config.id, mongodb_client)

        return mongodb_clients_repo

    def add_mongodb_client(self, id: ObjectId, client: MongoClient):
        """
        Adds a MongoDB client to the repository.

        Args:
            id (ObjectId): The ID of the client.
            client (MongoClient): The MongoDB client.

        Raises:
            ValueError: If ID already exists.
        """
        if self.__transaction_in_progress:
            raise ValueError("Transaction is still in progress")

        str_id = str(id)
        if str_id in self.__id_to_client:
            raise ValueError(f"Mongo DB Client ID {id} already exists")

        self.__id_to_client[str_id] = client

    def get_client_by_id(self, id: ObjectId) -> MongoClient:
        """
        Gets a MongoDB client from the repository.

        Args:
            id (ObjectId): The ID of the client.

        Raises:
            ValueError: If ID does not exist.
        """
        str_id = str(id)
        if str_id not in self.__id_to_client:
            raise ValueError(f"Cannot find MongoDB client {id}")
        return self.__id_to_client[str_id]

    def get_all_clients(self) -> list[tuple[ObjectId, MongoClient]]:
        """
        Returns all MongoDB client from the repository.

        Returns:
            ist[(ObjectId, MongoClient)]: A list of clients with their ids
        """
        return [(ObjectId(id), client) for id, client in self.__id_to_client.items()]

    @override
    def start_transactions(self):
        if self.__transaction_in_progress:
            raise ValueError("Transaction already in progress")

        self.__transaction_in_progress = True
        for client_id, client in self.get_all_clients():
            session = client.start_session()
            session.start_transaction(
                ReadConcern(level="snapshot"), WriteConcern(w="majority")
            )
            self.__client_id_to_session[client_id] = session

    @override
    def get_session_for_client_id(self, client_id: ObjectId) -> ClientSession | None:
        return self.__client_id_to_session.get(client_id, None)

    @override
    def commit_and_end_transactions(self):
        if not self.__transaction_in_progress:
            raise ValueError("Transaction not in progress")

        for client_id, session in self.__client_id_to_session.items():
            if session.in_transaction:
                logger.debug(f"Commiting transaction for {client_id}")
                session.commit_transaction()
            session.end_session()

        self.__client_id_to_session.clear()
        self.__transaction_in_progress = False

    @override
    def abort_and_end_transactions(self):
        if not self.__transaction_in_progress:
            raise ValueError("Transaction not in progress")

        for client_id, session in self.__client_id_to_session.items():
            if session.in_transaction:
                logger.debug(f"Ending transaction for {client_id}")
                session.abort_transaction()
            session.end_session()

        self.__client_id_to_session.clear()
        self.__transaction_in_progress = False
