from prettytable import PrettyTable

from ..shared.gphotos.clients_repository import GPhotosClientsRepository
from ..shared.mongodb.clients_repository import BYTES_512MB
from ..shared.config.config import Config
from pymongo.mongo_client import MongoClient


class UsageHandler:
    def run(self, config: Config):
        print(self.__get_mongodb_accounts_table(config))
        print("")

        gphotos_repo = GPhotosClientsRepository.build_from_config_repo(config)
        print(self.__get_gphoto_clients_table(gphotos_repo))

    def __get_mongodb_accounts_table(self, config: Config) -> PrettyTable:
        table = PrettyTable(title="MongoDB accounts")
        table.field_names = [
            "ID",
            "Name",
            "Free space remaining",
            "Usage",
            "Number of objects",
        ]
        for mongodb_config in config.get_mongodb_configs():
            client: MongoClient = MongoClient(
                mongodb_config.read_write_connection_string
            )
            db = client["sharded_google_photos"]
            db_stats = db.command({"dbStats": 1, 'freeStorage': 1})
            raw_total_free_storage = db_stats["totalFreeStorageSize"]
            usage = db_stats["storageSize"]
            num_objects = db_stats['objects']

            free_space = raw_total_free_storage
            if raw_total_free_storage == 0:
                free_space = BYTES_512MB - usage

            table.add_row(
                [mongodb_config.id, mongodb_config.name, free_space, usage, num_objects]
            )

        # Left align the columns
        for col in table.align:
            table.align[col] = "l"

        return table

    def __get_gphoto_clients_table(
        self, gphotos_repo: GPhotosClientsRepository
    ) -> PrettyTable:
        table = PrettyTable(title="Google Photos clients")
        table.field_names = [
            "ID",
            "Name",
            "Free space remaining",
            "Amount in trash",
            "Usage",
        ]

        for client_id, client in gphotos_repo.get_all_clients():
            storage_quota = client.get_storage_quota()
            table.add_row(
                [
                    client_id,
                    client.name(),
                    storage_quota.usage,
                    storage_quota.usage_in_drive_trash,
                    storage_quota.limit,
                ]
            )

        # Left align the columns
        for col in table.align:
            table.align[col] = "l"

        return table
