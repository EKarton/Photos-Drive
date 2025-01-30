import logging

from ..cli2.shared.printer import pretty_print_processed_diffs

from ..cli2.shared.inputs import (
    prompt_user_for_yes_no_answer,
)
from ..cli2.shared.files import (
    get_media_file_paths_from_path,
)
from ..shared.config.config import Config
from ..shared.mongodb.clients_repository import MongoDbClientsRepository
from ..shared.mongodb.albums_repository import AlbumsRepositoryImpl
from ..shared.mongodb.media_items_repository import MediaItemsRepositoryImpl
from ..shared.gphotos.clients_repository import GPhotosClientsRepository
from ..backup.diffs import Diff
from ..backup.processed_diffs import DiffsProcessor
from ..backup.backup_photos import PhotosBackup

logger = logging.getLogger(__name__)


class AddHandler:
    """A class that handles adding content from cli."""

    def add(self, path: str, config: Config, parallelize_uploads: bool):
        """
        Adds content to the system.

        Args:
            path (str): The path to the media items to add.
            config_file_path (str): The file path to the config file.
            parallelize_uploads (bool): Whether to parallelize uploads or not.
        """
        # Set up the repos
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphoto_clients_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Get the diffs
        diffs = [
            Diff(modifier="+", file_path=path)
            for path in get_media_file_paths_from_path(path)
        ]

        # Process the diffs with metadata
        diff_processor = DiffsProcessor()
        processed_diffs = diff_processor.process_raw_diffs(diffs)
        for processed_diff in processed_diffs:
            logger.debug(f"Processed diff: {processed_diff}")

        # Confirm if diffs are correct by the user
        pretty_print_processed_diffs(processed_diffs)
        if not prompt_user_for_yes_no_answer("Is this correct? (Y/N): "):
            print("Operation cancelled.")
            return

        # Process the diffs
        backup_service = PhotosBackup(
            config,
            albums_repo,
            media_items_repo,
            gphoto_clients_repo,
            mongodb_clients_repo,
            parallelize_uploads,
        )
        backup_results = backup_service.backup(processed_diffs)
        logger.debug(f"Backup results: {backup_results}")

        print(f"Added {len(diffs)} items.")
        print(f"Items added: {backup_results.num_media_items_added}")
        print(f"Items deleted: {backup_results.num_media_items_deleted}")
        print(f"Albums created: {backup_results.num_albums_created}")
        print(f"Albums deleted: {backup_results.num_albums_deleted}")
