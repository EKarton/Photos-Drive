import logging

from ..clean.clean_system import SystemCleaner
from ..shared.config.config import Config
from ..shared.mongodb.clients_repository import MongoDbClientsRepository
from ..shared.mongodb.albums_repository import AlbumsRepositoryImpl
from ..shared.mongodb.media_items_repository import MediaItemsRepositoryImpl
from ..shared.gphotos.clients_repository import GPhotosClientsRepository

logger = logging.getLogger(__name__)


class CleanHandler:
    """A class that handles cleaning up sharded google photos from cli."""

    def clean(self, config: Config):
        """
        Cleans the system.

        Args:
            config (Config): The config object
        """
        # Set up the repos
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        gphoto_clients_repo = GPhotosClientsRepository.build_from_config_repo(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        # Clean up
        cleaner = SystemCleaner(
            config,
            albums_repo,
            media_items_repo,
            gphoto_clients_repo,
            mongodb_clients_repo,
        )
        cleanup_results = cleaner.clean()

        print("Cleanup success!")
        print(
            f"Number of media items deleted: {cleanup_results.num_media_items_deleted}"
        )
        print(f"Number of albums deleted: {cleanup_results.num_albums_deleted}")
        print(
            "Number of Google Photos items trashed: "
            + str(cleanup_results.num_gmedia_items_moved_to_trash)
        )
