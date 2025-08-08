from collections import deque
import logging
from typing import cast

from tqdm import tqdm
import typer
from typing_extensions import Annotated

from photos_drive.shared.llm.models.open_clip_image_embeddings import (
    OpenCLIPImageEmbeddings,
)
from photos_drive.shared.llm.vector_stores.base_vector_store import (
    UpdateMediaItemEmbeddingRequest,
)
from photos_drive.shared.llm.vector_stores.distributed_vector_store import (
    DistributedVectorStore,
)
from photos_drive.shared.llm.vector_stores.vector_store_builder import (
    config_to_vector_store,
)

from ....shared.metadata.album_id import AlbumId
from ....shared.metadata.media_items_repository import (
    FindMediaItemRequest,
)
from ....shared.metadata.mongodb.albums_repository_impl import (
    AlbumsRepositoryImpl,
)
from ....shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from ....shared.metadata.mongodb.media_items_repository_impl import (
    MediaItemsRepositoryImpl,
)
from ...shared.config import build_config_from_options
from ...shared.inputs import (
    prompt_user_for_yes_no_answer,
)
from ...shared.logging import setup_logging
from ...shared.typer import (
    createMutuallyExclusiveGroup,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def copy_date_taken_to_vector_store(
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
        "Called db copy-date-taken-to-vector-store handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
    albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
    media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
    image_embedder = OpenCLIPImageEmbeddings()
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

    updates: list[UpdateMediaItemEmbeddingRequest] = []

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
                if media_item.embedding_id:
                    updates.append(
                        UpdateMediaItemEmbeddingRequest(
                            embedding_id=media_item.embedding_id,
                            new_date_taken=media_item.date_taken,
                        )
                    )
                    pbar.update(1)

    if not prompt_user_for_yes_no_answer(f'Update {len(updates)} embeddings? [Y/N]:'):
        raise ValueError("Operation cancelled")

    vector_store.update_media_item_embeddings(updates)
    print("Updated embeddings")
