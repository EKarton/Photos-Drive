import logging
import math
from typing import Generator

import typer
from typing_extensions import Annotated

from photos_drive.backup.backup_photos import (
    BackupResults,
    PhotosBackup,
)
from photos_drive.backup.diffs import Diff
from photos_drive.backup.processed_diffs import (
    DiffsProcessor,
    ProcessedDiff,
)
from photos_drive.cli.shared.config import build_config_from_options
from photos_drive.cli.shared.inputs import (
    prompt_user_for_yes_no_answer,
)
from photos_drive.cli.shared.logging import setup_logging
from photos_drive.cli.shared.printer import (
    pretty_print_diffs,
)
from photos_drive.cli.shared.typer import (
    createMutuallyExclusiveGroup,
)
from photos_drive.diff.get_diffs import DiffResults, FolderSyncDiff
from photos_drive.shared.blob_store.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from photos_drive.shared.config.config import Config
from photos_drive.shared.llm.models.blip_image_captions import BlipImageCaptions
from photos_drive.shared.llm.models.open_clip_image_embeddings import (
    OpenCLIPImageEmbeddings,
)
from photos_drive.shared.llm.vector_stores import vector_store_builder
from photos_drive.shared.llm.vector_stores.distributed_vector_store import (
    DistributedVectorStore,
)
from photos_drive.shared.maps.mongodb.map_cells_repository_impl import (
    MapCellsRepositoryImpl,
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
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def sync(
    local_dir_path: str,
    remote_albums_path: str = '',
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
    batch_size: Annotated[
        int,
        typer.Option(
            "--batch-size",
            help="The amount to batch the syncs",
        ),
    ] = 50,
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

    pretty_print_diffs(backup_diffs)
    if not prompt_user_for_yes_no_answer("Is this correct? (Y/N): "):
        print("Operation cancelled.")
        return

    diff_processor = DiffsProcessor(OpenCLIPImageEmbeddings(), BlipImageCaptions())
    processed_diffs = diff_processor.process_raw_diffs(backup_diffs)

    backup_results = __backup_diffs_to_system(
        config, processed_diffs, parallelize_uploads, batch_size
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
    batch_size: int,
) -> BackupResults:
    overall_results = BackupResults(0, 0, 0, 0, 0)
    num_total_chunks = math.ceil(len(processed_diffs) / batch_size)
    num_chunks_completed = 0

    for batch in __chunked(processed_diffs, batch_size):
        try:
            logger.info(f'Backing up chunk {num_chunks_completed} / {num_total_chunks}')
            mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
            gphoto_clients_repo = GPhotosClientsRepository.build_from_config(config)
            albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
            media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
            map_cells_repository = MapCellsRepositoryImpl(mongodb_clients_repo)
            vector_store = DistributedVectorStore(
                [
                    vector_store_builder.config_to_vector_store(vector_store_config)
                    for vector_store_config in config.get_vector_store_configs()
                ]
            )

            # Process the diffs
            backup_service = PhotosBackup(
                config,
                albums_repo,
                media_items_repo,
                map_cells_repository,
                vector_store,
                gphoto_clients_repo,
                mongodb_clients_repo,
                parallelize_uploads,
            )

            batch_results = backup_service.backup(batch)

            logger.info(f'Backed up {num_chunks_completed} / {num_total_chunks} chunks')
            logger.debug(f"Batch results: {batch_results}")

            num_chunks_completed += 1
            overall_results = __merge_results(overall_results, batch_results)

        except BaseException as e:
            logger.error(f'Chunk failed: {num_chunks_completed} / {num_total_chunks}')
            logger.error(e)

            logger.info(f"Albums created: {overall_results.num_albums_created}")
            logger.info(f"Albums deleted: {overall_results.num_albums_deleted}")
            logger.info(f"Media items created: {overall_results.num_media_items_added}")
            logger.info(
                f"Media items deleted: {overall_results.num_media_items_deleted}"
            )
            logger.info(
                f"Elapsed time: {overall_results.total_elapsed_time:.6f} seconds"
            )

            print("Run photos_drive_cli clean to fix errors")
            raise e

    logger.debug(f"Backup results: {overall_results}")
    return overall_results


def __merge_results(result1: BackupResults, result2: BackupResults) -> BackupResults:
    return BackupResults(
        num_media_items_added=result1.num_media_items_added
        + result2.num_media_items_added,
        num_media_items_deleted=result1.num_media_items_deleted
        + result2.num_media_items_deleted,
        num_albums_created=result1.num_albums_created + result2.num_albums_created,
        num_albums_deleted=result1.num_albums_deleted + result2.num_albums_deleted,
        total_elapsed_time=result1.total_elapsed_time + result2.total_elapsed_time,
    )


def __chunked(lst: list, size: int) -> Generator[list, None, None]:
    for i in range(0, len(lst), size):
        yield lst[i : i + size]
