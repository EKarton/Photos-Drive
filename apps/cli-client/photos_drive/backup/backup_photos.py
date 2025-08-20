from collections import deque
from dataclasses import dataclass, field
import logging
import time
from typing import Dict, Optional, cast

from bson.objectid import ObjectId

from photos_drive.backup.diffs_assignments import DiffsAssigner
from photos_drive.backup.gphotos_uploader import (
    GPhotosMediaItemParallelUploaderImpl,
    GPhotosMediaItemUploaderImpl,
    UploadRequest,
)
from photos_drive.backup.processed_diffs import ProcessedDiff
from photos_drive.shared.blob_store.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from photos_drive.shared.config.config import Config
from photos_drive.shared.llm.vector_stores.base_vector_store import (
    BaseVectorStore,
    CreateMediaItemEmbeddingRequest,
)
from photos_drive.shared.maps.map_cells_repository import MapCellsRepository
from photos_drive.shared.metadata.album_id import AlbumId
from photos_drive.shared.metadata.albums import Album
from photos_drive.shared.metadata.albums_pruner import AlbumsPruner
from photos_drive.shared.metadata.albums_repository import (
    AlbumsRepository,
)
from photos_drive.shared.metadata.clients_repository import (
    ClientsRepository,
)
from photos_drive.shared.metadata.media_items import MediaItem
from photos_drive.shared.metadata.media_items_repository import (
    CreateMediaItemRequest,
    FindMediaItemRequest,
    MediaItemsRepository,
)
from photos_drive.shared.metadata.transactions_context import TransactionsContext

logger = logging.getLogger(__name__)


@dataclass
class BackupResults:
    """
    Stores the results of the backup.

    Attributes:
        num_media_items_added (int): The number of media items added.
        num_media_items_deleted (int): The number of media items deleted.
        num_albums_created (int): The number of albums created.
        num_albums_deleted (int): The number of albums deleted.
        total_elapsed_time (float): The total elapsed time for a backup() to finish,
            in seconds.
    """

    num_media_items_added: int
    num_media_items_deleted: int
    num_albums_created: int
    num_albums_deleted: int
    total_elapsed_time: float


@dataclass
class DiffsTreeNode:
    album_name: str = ""
    child_nodes: list["DiffsTreeNode"] = field(default_factory=list)
    modifier_to_diffs: Dict[str, list[ProcessedDiff]] = field(default_factory=dict)
    album: Optional[Album] = None


class PhotosBackup:
    def __init__(
        self,
        config: Config,
        albums_repo: AlbumsRepository,
        media_items_repo: MediaItemsRepository,
        map_cells_repo: MapCellsRepository,
        vector_store: BaseVectorStore,
        gphotos_client_repo: GPhotosClientsRepository,
        clients_repo: ClientsRepository,
        parallelize_uploads: bool = False,
    ):
        self.__config = config
        self.__albums_repo = albums_repo
        self.__media_items_repo = media_items_repo
        self.__map_cells_repo = map_cells_repo
        self.__vector_store = vector_store
        self.__diffs_assigner = DiffsAssigner(gphotos_client_repo)
        self.__albums_pruner = AlbumsPruner(
            config.get_root_album_id(), albums_repo, media_items_repo
        )

        logger.debug(f"Parallelizing uploads: {parallelize_uploads}")
        self.__gphotos_uploader = (
            GPhotosMediaItemParallelUploaderImpl(gphotos_client_repo)
            if parallelize_uploads
            else GPhotosMediaItemUploaderImpl(gphotos_client_repo)
        )

        self.__clients_repo = clients_repo

    def backup(self, diffs: list[ProcessedDiff]) -> BackupResults:
        """Backs up a list of media items based on a list of diffs.

        Args:
            diffs (list[ProcessedDiff]): A list of processed diffs.

        Returns:
            BackupResults: A set of results from the backup.
        """
        start_time = time.time()

        # Step 1: Determine which photo to add belongs to which Google Photos account
        diff_assignments = self.__diffs_assigner.get_diffs_assignments(diffs)
        logger.debug(f"Diff assignments: {diff_assignments}")

        # Step 2: Upload the photos to Google Photos
        upload_diff_to_gphotos_media_item_id = self.__upload_diffs_to_gphotos(
            diff_assignments
        )
        logger.debug(
            f"Added diffs to Google Photos: {upload_diff_to_gphotos_media_item_id}"
        )

        # Step 3: Build a tree of albums with diffs on their edge nodes
        root_diffs_tree_node = self.__build_diffs_tree(diffs)
        logger.debug(f"Finished creating initial diff tree: {root_diffs_tree_node}")

        # Step 4: Create the missing photo albums in Mongo DB from the diffs tree
        # and attach the albums from database to the DiffTree
        total_num_albums_created = self.__build_missing_albums(root_diffs_tree_node)
        logger.debug(f"Finished building missing albums: {total_num_albums_created}")

        # Step 5: Go through the tree and modify album's media item ids list
        add_diffs_to_media_item: Dict[ProcessedDiff, MediaItem] = {}
        total_media_items_to_delete: list[MediaItem] = []
        total_num_media_item_added = 0
        total_album_ids_to_prune: list[AlbumId] = []
        queue = deque([root_diffs_tree_node])
        while len(queue) > 0:
            cur_diffs_tree_node = queue.popleft()
            cur_album = cast(Album, cur_diffs_tree_node.album)

            add_diffs = cur_diffs_tree_node.modifier_to_diffs.get("+", [])
            delete_diffs = cur_diffs_tree_node.modifier_to_diffs.get("-", [])
            num_media_items = self.__media_items_repo.get_num_media_items_in_album(
                cur_album.id
            )

            # Step 5a: Find media items to delete
            file_names_to_delete_set = set([diff.file_name for diff in delete_diffs])
            for file_name in file_names_to_delete_set:
                for media_item in self.__media_items_repo.find_media_items(
                    FindMediaItemRequest(album_id=cur_album.id, file_name=file_name)
                ):
                    total_media_items_to_delete.append(media_item)
                    num_media_items -= 1

            # Step 5b: Find the media items to add to the album,
            # and create them and add it to the tiles repo
            for add_diff in add_diffs:
                create_media_item_request = CreateMediaItemRequest(
                    file_name=add_diff.file_name,
                    file_hash=add_diff.file_hash,
                    location=add_diff.location,
                    gphotos_client_id=diff_assignments[add_diff],
                    gphotos_media_item_id=upload_diff_to_gphotos_media_item_id[
                        add_diff
                    ],
                    album_id=cur_album.id,
                    width=add_diff.width,
                    height=add_diff.height,
                    date_taken=add_diff.date_taken,
                    embedding_id=None,
                )
                media_item = self.__media_items_repo.create_media_item(
                    create_media_item_request
                )

                add_diffs_to_media_item[add_diff] = media_item
                total_num_media_item_added += 1
                num_media_items += 1

            # Step 5c: Mark album to prune if it's empty
            if (
                num_media_items == 0
                and self.__albums_repo.count_child_albums(cur_album.id) == 0
            ):
                total_album_ids_to_prune.append(cur_album.id)

            for child_diff_tree_node in cur_diffs_tree_node.child_nodes:
                queue.append(child_diff_tree_node)

        # Step 6: Delete the media items marked for deletion
        self.__media_items_repo.delete_many_media_items(
            [media_item.id for media_item in total_media_items_to_delete]
        )

        # Step 7: Delete albums with no child albums and no media items
        total_num_albums_deleted = 0
        for album_id in total_album_ids_to_prune:
            with TransactionsContext(self.__clients_repo):
                logger.debug(f"Pruning {album_id}")
                total_num_albums_deleted += self.__albums_pruner.prune_album(album_id)

        # Step 8: Delete items from the maps
        for media_item in total_media_items_to_delete:
            self.__map_cells_repo.remove_media_item(media_item.id)

        # Step 9: Add items to the maps repo
        for media_item in add_diffs_to_media_item.values():
            if media_item.location:
                self.__map_cells_repo.add_media_item(media_item)

        # Step 10: Delete media items from vector store
        self.__vector_store.delete_media_item_embeddings_by_media_item_ids(
            [media_item.id for media_item in total_media_items_to_delete]
        )

        # Step 11: Add media items with embeddings to vector store
        create_media_item_embedding_requests: list[CreateMediaItemEmbeddingRequest] = []
        for add_diff, media_item in add_diffs_to_media_item.items():
            media_item = add_diffs_to_media_item[add_diff]
            create_media_item_embedding_requests.append(
                CreateMediaItemEmbeddingRequest(
                    embedding=add_diff.embedding,
                    media_item_id=media_item.id,
                    date_taken=add_diff.date_taken,
                )
            )
        self.__vector_store.add_media_item_embeddings(
            create_media_item_embedding_requests
        )

        # Step 8: Return the results of the backup
        return BackupResults(
            num_media_items_added=total_num_media_item_added,
            num_media_items_deleted=len(total_media_items_to_delete),
            num_albums_created=total_num_albums_created,
            num_albums_deleted=total_num_albums_deleted,
            total_elapsed_time=time.time() - start_time,
        )

    def __build_diffs_tree(self, diffs: list[ProcessedDiff]) -> DiffsTreeNode:
        """
        Builds a diff tree from the album heirarchy in the list of diffs.

        Args:
            diffs (list[ProcessedDiff]): A list of diffs.

        Returns:
            DiffsTreeNode: The root of the diff tree.
        """
        root_diffs_tree_node = DiffsTreeNode()
        for diff in diffs:
            albums_queue = deque(diff.album_name.split("/"))
            cur_diffs_tree_node = root_diffs_tree_node

            while len(albums_queue) > 0:
                cur_album = albums_queue.popleft()
                child_album_node = None
                for child_node in cur_diffs_tree_node.child_nodes:
                    if child_node.album_name == cur_album:
                        child_album_node = child_node
                        break

                if not child_album_node:
                    child_album_node = DiffsTreeNode(album_name=cur_album)
                    cur_diffs_tree_node.child_nodes.append(child_album_node)

                cur_diffs_tree_node = child_album_node

            if diff.modifier not in cur_diffs_tree_node.modifier_to_diffs:
                cur_diffs_tree_node.modifier_to_diffs[diff.modifier] = []

            cur_diffs_tree_node.modifier_to_diffs[diff.modifier].append(diff)

        return root_diffs_tree_node

    def __build_missing_albums(self, diff_tree: DiffsTreeNode) -> int:
        """
        Creates albums that are missing from the diff tree.

        Args:
            diff_tree (DiffsTreeNode): The root of the diff tree.

        Returns:
            int: The total number of new albums created.
        """
        num_albums_created = 0
        root_album_id = self.__config.get_root_album_id()
        root_album = self.__albums_repo.get_album_by_id(root_album_id)
        queue = deque([(diff_tree, root_album)])

        while len(queue) > 0:
            cur_diffs_tree_node, cur_album = queue.popleft()
            cur_diffs_tree_node.album = cur_album

            child_album_name_to_album: Dict[str, Album] = {}
            for child_album in self.__albums_repo.find_child_albums(cur_album.id):
                child_album_name_to_album[cast(str, child_album.name)] = child_album

            with TransactionsContext(self.__clients_repo):
                for child_diff_node in cur_diffs_tree_node.child_nodes:
                    if child_diff_node.album_name not in child_album_name_to_album:
                        new_album = self.__albums_repo.create_album(
                            album_name=child_diff_node.album_name,
                            parent_album_id=cur_album.id,
                        )
                        num_albums_created += 1
                        child_album_name_to_album[child_diff_node.album_name] = (
                            new_album
                        )

                    child_album = child_album_name_to_album[child_diff_node.album_name]
                    queue.append((child_diff_node, child_album))

        return num_albums_created

    def __upload_diffs_to_gphotos(
        self, diff_assignments: Dict[ProcessedDiff, ObjectId]
    ) -> dict[ProcessedDiff, str]:
        """
        Uploads a map of diffs with their GPhotos client ID to Google Photos.
        It returns a map of diffs to their media item IDs on Google Photos.

        Args:
            diff_assignments (Dict[ProcessedDiff, ObjectId]):
                A set of diff assignments.

        Returns:
            dict[ProcessedDiff, str]: A map of diffs to their media item IDs on
                Google Photos.
        """
        diff_assignments_items = diff_assignments.items()
        upload_requests = [
            UploadRequest(
                file_path=diff.file_path,
                file_name=diff.file_name,
                gphotos_client_id=client_id,
            )
            for diff, client_id in diff_assignments_items
        ]
        gphotos_media_item_ids = self.__gphotos_uploader.upload_photos(upload_requests)
        assert len(gphotos_media_item_ids) == len(upload_requests)

        upload_diff_to_gphotos_media_item_id = {
            item[0]: gphotos_media_item_id
            for item, gphotos_media_item_id in zip(
                diff_assignments_items, gphotos_media_item_ids
            )
        }

        return upload_diff_to_gphotos_media_item_id
