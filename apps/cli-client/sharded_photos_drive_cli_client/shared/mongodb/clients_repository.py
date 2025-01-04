from typing import Dict

from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId

from ..config.config import Config


class MongoDbClientsRepository:
    def __init__(self):
        self.__id_to_client: Dict[str, MongoClient] = {}

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

        for id, mongodb_client in config.get_mongo_db_clients():
            mongodb_clients_repo.add_mongodb_client(id, mongodb_client)

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
            raise ValueError(f"Cannot find MongoDB client with ID {id}")
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
            db_stats = db.command("dbstats")
            used_space = db_stats["totalFreeStorageSize"]

            if used_space > most_unused_space:
                best_client_id = id
                most_unused_space = used_space

        if best_client_id is None:
            raise ValueError("No MongoDB Client!")

        return ObjectId(best_client_id)

    def get_all_clients(self) -> list[tuple[ObjectId, MongoClient]]:
        """
        Returns all MongoDB client from the repository.

        Returns:
            ist[(ObjectId, MongoClient)]: A list of clients with their ids
        """
        return [(ObjectId(id), client) for id, client in self.__id_to_client.items()]
