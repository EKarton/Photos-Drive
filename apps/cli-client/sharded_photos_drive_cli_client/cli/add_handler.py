import logging


from .utils import get_diffs_from_path
from ..shared.config.config_from_file import ConfigFromFile
from ..shared.mongodb.clients_repository import MongoDbClientsRepository
from ..shared.mongodb.albums_repository import AlbumsRepositoryImpl
from ..shared.mongodb.media_items_repository import MediaItemsRepositoryImpl
from ..shared.gphotos.clients_repository import GPhotosClientsRepository
from ..backup.diffs import Diff
from ..backup.processed_diffs import DiffsProcessor
from ..backup.backup_photos import PhotosBackup
from ..backup.diffs_assignments import DiffsAssigner
from ..backup.gphotos_uploader import GPhotosMediaItemUploader

logger = logging.getLogger(__name__)


class AddHandler:
    """A class that handles adding content from cli."""

    def add(self, path: str, config_file_path: str):
        """
        Adds content to the system.

        Args:
            path (str): The path to the media items to add.
            config_file_path (str): The file path to the config file.
        """
        # Set up the repos
        config = ConfigFromFile(config_file_path)
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphoto_clients_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Get the diffs
        diffs = [
            Diff(modifier="+", file_path=path) for path in get_diffs_from_path(path)
        ]

        # Process the diffs with metadata
        diff_processor = DiffsProcessor()
        processed_diffs = diff_processor.process_raw_diffs(diffs)
        for processed_diff in processed_diffs:
            logger.debug(f"Processed diff: {processed_diff}")

        # Process the diffs
        gphotos_uploader = GPhotosMediaItemUploader(gphoto_clients_repo)
        diffs_assigner = DiffsAssigner(config)
        backup_service = PhotosBackup(
            config, albums_repo, media_items_repo, gphotos_uploader, diffs_assigner
        )
        backup_results = backup_service.backup(processed_diffs)
        logger.debug(f"Backup results: {backup_results}")
