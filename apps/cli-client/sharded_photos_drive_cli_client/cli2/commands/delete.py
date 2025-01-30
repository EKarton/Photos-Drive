import logging
from typing_extensions import Annotated
import typer

from sharded_photos_drive_cli_client.backup.backup_photos import PhotosBackup
from sharded_photos_drive_cli_client.backup.diffs import Diff
from sharded_photos_drive_cli_client.backup.processed_diffs import DiffsProcessor
from sharded_photos_drive_cli_client.cli2.shared.inputs import (
    prompt_user_for_yes_no_answer,
)
from sharded_photos_drive_cli_client.cli2.shared.printer import pretty_print_diffs
from sharded_photos_drive_cli_client.cli2.shared.files import (
    get_media_file_paths_from_path,
)
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
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def delete(
    path: str,
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
        "Called add handler with args:\n"
        + f" path: {path}\n"
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

    # Get the diffs
    diffs = [
        Diff(modifier="-", file_path=path)
        for path in get_media_file_paths_from_path(path)
    ]

    # Confirm if diffs are correct by the user
    pretty_print_diffs(diffs)
    if not prompt_user_for_yes_no_answer("Is this correct? (Y/N): "):
        print("Operation cancelled.")
        return

    # Process the diffs with metadata
    diff_processor = DiffsProcessor()
    processed_diffs = diff_processor.process_raw_diffs(diffs)
    for processed_diff in processed_diffs:
        logger.debug(f"Processed diff: {processed_diff}")

    # Process the diffs
    backup_service = PhotosBackup(
        config,
        albums_repo,
        media_items_repo,
        gphoto_clients_repo,
        mongodb_clients_repo,
    )
    backup_results = backup_service.backup(processed_diffs)
    logger.debug(f"Backup results: {backup_results}")

    print(f"Deleted {len(diffs)} items.")
    print(f"Items added: {backup_results.num_media_items_added}")
    print(f"Items deleted: {backup_results.num_media_items_deleted}")
    print(f"Albums created: {backup_results.num_albums_created}")
    print(f"Albums deleted: {backup_results.num_albums_deleted}")
