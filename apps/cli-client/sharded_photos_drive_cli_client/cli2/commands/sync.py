import logging
from typing_extensions import Annotated
import typer

from sharded_photos_drive_cli_client.backup.backup_photos import (
    BackupResults,
    PhotosBackup,
)
from sharded_photos_drive_cli_client.backup.diffs import Diff
from sharded_photos_drive_cli_client.backup.processed_diffs import (
    DiffsProcessor,
    ProcessedDiff,
)
from sharded_photos_drive_cli_client.cli2.shared.inputs import (
    prompt_user_for_yes_no_answer,
)
from sharded_photos_drive_cli_client.cli2.shared.printer import (
    pretty_print_processed_diffs,
)
from sharded_photos_drive_cli_client.cli2.shared.config import build_config_from_options
from sharded_photos_drive_cli_client.cli2.shared.logging import setup_logging
from sharded_photos_drive_cli_client.cli2.shared.typer import (
    createMutuallyExclusiveGroup,
)
from sharded_photos_drive_cli_client.diff.get_diffs import DiffResults, FolderSyncDiff
from sharded_photos_drive_cli_client.shared.config.config import Config
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
def sync(
    local_dir_path: str,
    remote_albums_path: str,
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
    parallelize_uploads: Annotated[
        bool,
        typer.Option(
            "--parallelize-uploads",
            help="Whether to parallelize uploads or not",
        ),
    ] = False,
):
    setup_logging(verbose)

    logger.debug(
        "Called sync handler with args:\n"
        + f" local_dir_path: {local_dir_path}\n"
        + f" remote_albums_path: {remote_albums_path}\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}\n"
        + f" parallelize_uploads={parallelize_uploads}"
    )

    config = build_config_from_options(config_file, config_mongodb)
    mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
    diff_comparator = FolderSyncDiff(
        config=config,
        albums_repo=AlbumsRepositoryImpl(mongodb_clients_repo),
        media_items_repo=MediaItemsRepositoryImpl(mongodb_clients_repo),
    )
    diff_results = diff_comparator.get_diffs(local_dir_path, remote_albums_path)
    logger.debug(f'Diff results: {diff_results}')

    backup_diffs = __convert_diff_results_to_backup_diffs(diff_results)
    if len(backup_diffs) == 0:
        print("No changes")
        return

    diff_processor = DiffsProcessor()
    processed_diffs = diff_processor.process_raw_diffs(backup_diffs)

    pretty_print_processed_diffs(processed_diffs)
    if not prompt_user_for_yes_no_answer("Is this correct? (Y/N): "):
        print("Operation cancelled.")
        return

    backup_results = __backup_diffs_to_system(
        config, processed_diffs, parallelize_uploads
    )
    print("Sync complete.")
    print(f"Albums created: {backup_results.num_albums_created}")
    print(f"Albums deleted: {backup_results.num_albums_deleted}")
    print(f"Media items created: {backup_results.num_media_items_added}")
    print(f"Media items deleted: {backup_results.num_media_items_deleted}")
    print(f"Elapsed time: {backup_results.total_elapsed_time:.6f} seconds")


def __convert_diff_results_to_backup_diffs(diff_results: DiffResults) -> list[Diff]:
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
