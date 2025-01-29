from prettytable import PrettyTable

from ..shared.gphotos.clients_repository import GPhotosClientsRepository
from ..shared.mongodb.clients_repository import MongoDbClientsRepository
from ..shared.config.config import Config


class UsageHandler:
    def run(self, config: Config):
        mongodb_repo = MongoDbClientsRepository.build_from_config(config)
        gphotos_repo = GPhotosClientsRepository.build_from_config_repo(config)

        print(self.__get_mongodb_accounts_table(mongodb_repo))
        print("")
        print(self.__get_gphoto_clients_table(gphotos_repo))

    def __get_mongodb_accounts_table(
        self, mongodb_repo: MongoDbClientsRepository
    ) -> PrettyTable:
        table = PrettyTable(title="MongoDB accounts")
        table.field_names = [
            "ID",
            "Name",
            "Free space remaining",
            "Usage",
            "Number of objects",
        ]
        for client_id, client in mongodb_repo.get_all_clients():
            db_stats = client["sharded_google_photos"].command("dbstats")

            free_space_remaining = db_stats['totalFreeStorageSize']
            usage = db_stats['dataSize']
            num_objects = db_stats['objects']

            table.add_row([client_id, "TBD", free_space_remaining, usage, num_objects])

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
