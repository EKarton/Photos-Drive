import logging

from sharded_photos_drive_cli_client.shared.mongodb.albums_repository import (
    AlbumsRepositoryImpl,
)
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.media_items_repository import (
    MediaItemsRepositoryImpl,
)
from ..backup.diffs import Diff
from ..backup.processed_diffs import ProcessedDiff, DiffsProcessor
from ..diff.get_diffs import PhotosDiff, DiffResults
from ..shared.config.config import Config

logger = logging.getLogger(__name__)


class SyncHandler:
    """A class that handles syncing content from local to remote via cli."""

    def sync(self, local_dir_path: str, remote_albums_path: str, config: Config):
        """
        Adds content to the system.

        Args:
            path (str): The path to the media items to add.
            config_file_path (str): The file path to the config file.
        """
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        photo_diff = PhotosDiff(
            config=config,
            albums_repo=AlbumsRepositoryImpl(mongodb_clients_repo),
            media_items_repo=MediaItemsRepositoryImpl(mongodb_clients_repo),
        )
        diff_results = photo_diff.get_diffs(local_dir_path, remote_albums_path)
        logger.debug(f'Diff results: {diff_results}')

        backup_diffs = self.__convert_diff_results_to_backup_diffs(diff_results)
        logger.debug(f'Backup diffs: {backup_diffs}')

        if len(backup_diffs) == 0:
            print("No changes")
            return

        self.__print_backup_diffs(backup_diffs)

    def __convert_diff_results_to_backup_diffs(
        self, diff_results: DiffResults
    ) -> list[Diff]:
        backup_diffs: list[Diff] = []

        for remote_file in diff_results.missing_remote_files_in_local:
            backup_diffs.append(
                Diff(modifier='-', file_path=remote_file.remote_relative_file_path)
            )

        for local_file in diff_results.missing_local_files_in_remote:
            backup_diffs.append(
                Diff(modifier='+', file_path=local_file.local_relative_file_path)
            )

        return backup_diffs

    def __print_backup_diffs(self, backup_diffs: list[Diff]):
        sorted_backup_diffs = sorted(backup_diffs, key=lambda obj: obj.file_path)
        print(sorted_backup_diffs)
