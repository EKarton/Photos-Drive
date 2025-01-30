import logging

from ..cli2.shared.inputs import (
    prompt_user_for_yes_no_answer,
)
from ..backup.backup_photos import PhotosBackup, BackupResults
from ..shared.gphotos.clients_repository import GPhotosClientsRepository
from ..shared.mongodb.albums_repository import AlbumsRepositoryImpl
from ..shared.mongodb.clients_repository import MongoDbClientsRepository
from ..shared.mongodb.media_items_repository import MediaItemsRepositoryImpl
from ..backup.diffs import Diff
from ..backup.processed_diffs import DiffsProcessor, ProcessedDiff
from ..diff.get_diffs import FolderSyncDiff, DiffResults
from ..shared.config.config import Config
from ..cli2.shared.printer import pretty_print_processed_diffs

logger = logging.getLogger(__name__)


class SyncHandler:
    """A class that handles syncing content from local to remote via cli."""

    def sync(
        self,
        local_dir_path: str,
        remote_albums_path: str,
        config: Config,
        parallelize_uploads: bool,
    ):
        """
        Adds content to the system.

        Args:
            path (str): The path to the media items to add.
            config_file_path (str): The file path to the config file.
            parallelize_uploads (bool): Whether to parallelize uploads or not.
        """
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        diff_comparator = FolderSyncDiff(
            config=config,
            albums_repo=AlbumsRepositoryImpl(mongodb_clients_repo),
            media_items_repo=MediaItemsRepositoryImpl(mongodb_clients_repo),
        )
        diff_results = diff_comparator.get_diffs(local_dir_path, remote_albums_path)
        logger.debug(f'Diff results: {diff_results}')

        backup_diffs = self.__convert_diff_results_to_backup_diffs(diff_results)
        if len(backup_diffs) == 0:
            print("No changes")
            return

        diff_processor = DiffsProcessor()
        processed_diffs = diff_processor.process_raw_diffs(backup_diffs)

        pretty_print_processed_diffs(processed_diffs)
        if not prompt_user_for_yes_no_answer("Is this correct? (Y/N): "):
            print("Operation cancelled.")
            return

        backup_results = self.__backup_diffs_to_system(
            config, processed_diffs, parallelize_uploads
        )
        print("Sync complete.")
        print(f"Albums created: {backup_results.num_albums_created}")
        print(f"Albums deleted: {backup_results.num_albums_deleted}")
        print(f"Media items created: {backup_results.num_media_items_added}")
        print(f"Media items deleted: {backup_results.num_media_items_deleted}")
        print(f"Elapsed time: {backup_results.total_elapsed_time:.6f} seconds")

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

    def __backup_diffs_to_system(
        self,
        config: Config,
        processed_diffs: list[ProcessedDiff],
        parallelize_uploads: bool,
    ) -> BackupResults:
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphoto_clients_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Process the diffs
        backup_service = PhotosBackup(
            config,
            albums_repo,
            media_items_repo,
            gphoto_clients_repo,
            mongodb_clients_repo,
            parallelize_uploads,
        )
        try:
            backup_results = backup_service.backup(processed_diffs)
            logger.debug(f"Backup results: {backup_results}")
            return backup_results
        except BaseException as e:
            logger.error(f'Backup failed: {e}')
            print("Run sharded_photos_drive clean to fix errors")
            raise e
