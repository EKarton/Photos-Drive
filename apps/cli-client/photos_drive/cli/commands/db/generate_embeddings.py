from collections import deque
import logging
from typing import cast

from tqdm import tqdm
import typer
from typing_extensions import Annotated

from photos_drive.backup.diffs import Diff
from photos_drive.backup.processed_diffs import DiffsProcessor
from photos_drive.cli.shared.config import build_config_from_options
from photos_drive.cli.shared.inputs import (
    prompt_user_for_yes_no_answer,
)
from photos_drive.cli.shared.logging import setup_logging
from photos_drive.cli.shared.typer import (
    createMutuallyExclusiveGroup,
)
from photos_drive.shared.llm.models.blip_image_captions import BlipImageCaptions
from photos_drive.shared.llm.models.open_clip_image_embeddings import (
    OpenCLIPImageEmbeddings,
)
from photos_drive.shared.llm.vector_stores.base_vector_store import (
    CreateMediaItemEmbeddingRequest,
)
from photos_drive.shared.llm.vector_stores.distributed_vector_store import (
    DistributedVectorStore,
)
from photos_drive.shared.llm.vector_stores.vector_store_builder import (
    config_to_vector_store,
)
from photos_drive.shared.metadata.album_id import AlbumId
from photos_drive.shared.metadata.media_item_id import MediaItemId
from photos_drive.shared.metadata.media_items_repository import (
    FindMediaItemRequest,
    UpdateMediaItemRequest,
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
def generate_embeddings(
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
        "Called db generate-embeddings handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    image_embedder = OpenCLIPImageEmbeddings()
    image_captions = BlipImageCaptions()

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
    albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
    media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
    vector_store = DistributedVectorStore(
        stores=[
            config_to_vector_store(
                config, embedding_dimensions=image_embedder.get_embedding_dimension()
            )
            for config in config.get_vector_store_configs()
        ]
    )

    root_album_id = config.get_root_album_id()
    albums_queue: deque[tuple[AlbumId, list[str]]] = deque([(root_album_id, [])])
    diffs: list[Diff] = []
    media_item_ids: list[MediaItemId] = []

    with tqdm(desc="Finding media items") as pbar:
        while len(albums_queue) > 0:
            album_id, prev_albums_path = albums_queue.popleft()
            album = albums_repo.get_album_by_id(album_id)

            for child_album in albums_repo.find_child_albums(album.id):
                if album_id == root_album_id:
                    albums_queue.append((child_album.id, prev_albums_path + ['.']))
                else:
                    albums_queue.append(
                        (child_album.id, prev_albums_path + [cast(str, album.name)])
                    )

            for media_item in media_items_repo.find_media_items(
                FindMediaItemRequest(album_id=album_id)
            ):
                if album_id == root_album_id:
                    file_path = '/'.join(prev_albums_path + [media_item.file_name])
                else:
                    file_path = '/'.join(
                        prev_albums_path + [cast(str, album.name), media_item.file_name]
                    )

                diffs.append(
                    Diff(
                        modifier='+',
                        file_path=file_path,
                        width=media_item.width,
                        height=media_item.height,
                        date_taken=media_item.date_taken,
                        location=media_item.location,
                    )
                )
                media_item_ids.append(media_item.id)
                pbar.update(1)

    print(f"Need to generate {len(diffs)} embeddings")

    diffs_processor = DiffsProcessor(
        image_embedder=image_embedder,
        image_captions=image_captions,
    )
    processed_diffs = diffs_processor.process_raw_diffs(diffs)

    assert len(media_item_ids) == len(diffs) == len(processed_diffs)

    for diff in processed_diffs:
        print(f"{diff.file_name} -> {diff.captions}")

    if not prompt_user_for_yes_no_answer('Add embeddings to metadata db? [Y/N]:'):
        raise ValueError("Operation cancelled")

    vector_store.delete_all_media_item_embeddings()
    print("Deleted all existing embeddings in vector store")

    create_media_item_embedding_req: list[CreateMediaItemEmbeddingRequest] = [
        CreateMediaItemEmbeddingRequest(
            embedding=processed_diff.embedding,
            media_item_id=media_item_id,
            date_taken=processed_diff.date_taken,
        )
        for media_item_id, processed_diff in zip(media_item_ids, processed_diffs)
    ]
    media_item_embeddings = vector_store.add_media_item_embeddings(
        create_media_item_embedding_req
    )
    print("Added embeddings to vector store")

    update_media_item_requests: list[UpdateMediaItemRequest] = [
        UpdateMediaItemRequest(
            media_item_id=media_item_embedding.media_item_id,
            new_embedding_id=media_item_embedding.id,
        )
        for media_item_embedding in media_item_embeddings
    ]
    media_items_repo.update_many_media_items(update_media_item_requests)
    print("Updated media items store with embedding references")
