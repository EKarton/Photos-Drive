import logging

import typer
from typing_extensions import Annotated

from photos_drive.clean.clean_system import SystemCleaner
from photos_drive.cli.shared.config import build_config_from_options
from photos_drive.cli.shared.inputs import prompt_user_for_yes_no_answer
from photos_drive.cli.shared.logging import setup_logging
from photos_drive.cli.shared.printer import pretty_print_items_to_delete
from photos_drive.cli.shared.typer import (
    createMutuallyExclusiveGroup,
)
from photos_drive.shared.blob_store.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from photos_drive.shared.metadata.mongodb.albums_repository_impl import (
    AlbumsRepositoryImpl,
)
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.mongodb.media_items_repository_impl import (
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
    gphoto_clients_repo = GPhotosClientsRepository.build_from_config(config)
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
    items_to_delete = cleaner.find_item_to_delete()
    pretty_print_items_to_delete(items_to_delete)
    if not prompt_user_for_yes_no_answer("Is this correct? (Y/N): "):
        print("Operation cancelled.")
        return

    cleanup_results = cleaner.delete_items(items_to_delete)

    typer.echo("Cleanup success!")
    typer.echo(
        f"Number of media items deleted: {cleanup_results.num_media_items_deleted}"
    )
    typer.echo(f"Number of albums deleted: {cleanup_results.num_albums_deleted}")
    typer.echo(
        "Number of Google Photos items trashed: "
        + str(cleanup_results.num_gmedia_items_moved_to_trash)
    )
