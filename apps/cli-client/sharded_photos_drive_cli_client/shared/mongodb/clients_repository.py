import logging
from types import TracebackType
from typing import Dict
from pymongo.mongo_client import MongoClient
from pymongo.client_session import ClientSession
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from bson.objectid import ObjectId

from ..config.config import Config

logger = logging.getLogger(__name__)

BYTES_512MB = 536870912


class MongoDbClientsRepository:
    def __init__(self):
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
        """
        Returns the client ID with the most amount of space.

        Returns:
            ObjectId: the client ID with the most amount of space.
        """
        best_client_id = None
        most_unused_space = float("-inf")

        for id, client in self.__id_to_client.items():
            db = client["sharded_google_photos"]
            db_stats = db.command({'dbStats': 1, 'freeStorage': 1})
            raw_total_free_storage = db_stats["totalFreeStorageSize"]

            # Handle case of free tier: they return 0 for `totalFreeStorageSize`
            # even though it is 512 MB
            free_space = raw_total_free_storage
            if raw_total_free_storage == 0:
                free_space = BYTES_512MB - db_stats["storageSize"]

            if free_space <= 0:
                continue

            if free_space > most_unused_space:
                best_client_id = id
                most_unused_space = free_space

        if best_client_id is None:
            raise ValueError("No MongoDB client found with free space!")

        return ObjectId(best_client_id)

    def get_all_clients(self) -> list[tuple[ObjectId, MongoClient]]:
        """
        Returns all MongoDB client from the repository.

        Returns:
            ist[(ObjectId, MongoClient)]: A list of clients with their ids
        """
        return [(ObjectId(id), client) for id, client in self.__id_to_client.items()]

    def start_transactions(self):
        '''
        Starts a transaction.

        Database transactions are only saved if commit_and_end_transactions() is called.

        A call to abort_and_end_transactions() will abort and roll back all
        transactions.
        '''
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
        '''
        Commits the transactions and ends the session.
        Note: it must call start_transactions() first before calling this method.
        '''
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
        '''
        Aborts the transactions and ends the session.
        Note: it must call start_transactions() first before calling this method.
        '''
        if not self.__transaction_in_progress:
            raise ValueError("Transaction not in progress")

        for client_id, session in self.__client_id_to_session.items():
            if session.in_transaction:
                logger.debug(f"Ending transaction for {client_id}")
                session.abort_transaction()
            session.end_session()

        self.__client_id_to_session.clear()
        self.__transaction_in_progress = False


class MongoDbTransactionsContext:
    def __init__(self, repo: MongoDbClientsRepository):
        self.__repo = repo

    def __enter__(self):
        self.__repo.start_transactions()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        if exc_type:
            logger.error(f"Aborting transaction due to error: {exc_value}")
            self.__repo.abort_and_end_transactions()
            logger.error("Transaction aborted")
        else:
            self.__repo.commit_and_end_transactions()
            logger.debug("Commited transactions")
