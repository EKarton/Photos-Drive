import logging
from typing import Dict

from bson.objectid import ObjectId
from pymongo.client_session import ClientSession
from pymongo.mongo_client import MongoClient
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

from photos_drive.shared.config.config import Config
from photos_drive.shared.metadata.clients_repository import (
    ClientsRepository,
)

logger = logging.getLogger(__name__)

BYTES_512MB = 536870912


class MongoDbClientsRepository(ClientsRepository):
    def __init__(self) -> None:
        self.__id_to_client: Dict[str, MongoClient] = {}
        self.__client_id_to_session: dict[ObjectId, ClientSession] = {}
        self.__transaction_in_progress = False

    @staticmethod
    def build_from_config(
        config: Config,
    ) -> "MongoDbClientsRepository":
        """
        A factory method that builds the MongoDbClientsRepository from the config.

        Args:
            config (Config): The config

        Returns:
            MongoDbClientsRepository: An instance of the Mongo DB clients repo.
        """
        mongodb_clients_repo = MongoDbClientsRepository()

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

    def find_id_of_client_with_most_space(self) -> ObjectId:
        best_client_id = None
        most_unused_space = float("-inf")

        for client_id, free_space in self.get_free_space_for_all_clients():
            if free_space <= 0:
                continue

            if free_space > most_unused_space:
                best_client_id = client_id
                most_unused_space = free_space

        if best_client_id is None:
            raise ValueError("No MongoDB client found with free space!")

        return best_client_id

    def get_free_space_for_all_clients(self) -> list[tuple[ObjectId, int]]:
        free_spaces = []

        for client_id, client in self.__id_to_client.items():
            db = client["photos_drive"]
            db_stats = db.command({'dbStats': 1, 'freeStorage': 1})
            raw_total_free_storage = db_stats["totalFreeStorageSize"]

            # Handle case of free tier: they return 0 for `totalFreeStorageSize`
            # even though it is 512 MB
            free_space = raw_total_free_storage
            if raw_total_free_storage == 0:
                free_space = BYTES_512MB - db_stats["storageSize"]

            free_spaces.append((ObjectId(client_id), free_space))

        return free_spaces

    def get_all_clients(self) -> list[tuple[ObjectId, MongoClient]]:
        """
        Returns all MongoDB client from the repository.

        Returns:
            ist[(ObjectId, MongoClient)]: A list of clients with their ids
        """
        return [(ObjectId(id), client) for id, client in self.__id_to_client.items()]

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

    def get_session_for_client_id(self, client_id: ObjectId) -> ClientSession | None:
        '''
        Returns the MongoDB session for a ClientID.

        Args:
            client_id (ObjectId): The ID of the MongoDB client

        Returns:
            ClientSession | None: The session if it has already started; else None.
        '''
        return self.__client_id_to_session.get(client_id, None)

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
