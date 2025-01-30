import logging
from typing_extensions import Annotated
import typer

from sharded_photos_drive_cli_client.clean.clean_system import SystemCleaner
from sharded_photos_drive_cli_client.cli2.shared.config import build_config_from_options
from sharded_photos_drive_cli_client.cli2.shared.logging import setup_logging
from sharded_photos_drive_cli_client.cli2.shared.typer import (
    createMutuallyExclusiveGroup,
)
from sharded_photos_drive_cli_client.shared.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.albums_repository import (
    AlbumsRepositoryImpl,
)
from sharded_photos_drive_cli_client.shared.mongodb.clients_repository import (
    MongoDbClientsRepository,
)
from sharded_photos_drive_cli_client.shared.mongodb.media_items_repository import (
    MediaItemsRepositoryImpl,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup()


@app.command()
def clean(
    config_file: Annotated[
        str | None,
        typer.Option(
            "--config-file",
            help="Path to config file",
            callback=config_exclusivity_callback,
        ),
    ] = None,
    config_mongodb: Annotated[
        str | None,
        typer.Option(
            "--config-mongodb",
            help="Connection string to a MongoDB account that has the configs",
            is_eager=False,
            callback=config_exclusivity_callback,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Whether to show all logging debug statements or not",
        ),
    ] = False,
):
    setup_logging(verbose)

    logger.debug(
        "Called clean handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
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

    typer.echo("Cleanup success!")
    typer.echo(
        f"Number of media items deleted: {cleanup_results.num_media_items_deleted}"
    )
    typer.echo(f"Number of albums deleted: {cleanup_results.num_albums_deleted}")
    typer.echo(
        "Number of Google Photos items trashed: "
        + str(cleanup_results.num_gmedia_items_moved_to_trash)
    )
