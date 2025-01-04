from dataclasses import dataclass, field
from typing import Optional, Dict, cast
from collections import deque
import logging

from bson.objectid import ObjectId


from ..shared.config.config import Config
from ..shared.mongodb.albums import Album
from ..shared.mongodb.albums_repository import AlbumsRepository, UpdatedAlbumFields
from ..shared.mongodb.media_items import MediaItem, MediaItemId
from ..shared.mongodb.media_items_repository import MediaItemsRepository
from ..shared.mongodb.media_items_repository import CreateMediaItemRequest

from .processed_diffs import ProcessedDiff
from .gphotos_uploader import GPhotosMediaItemUploader, UploadRequest
from .diffs_assignments import DiffsAssigner

logger = logging.getLogger(__name__)


@dataclass
class BackupResults:
    """
    Stores the results of the backup.

    Attributes:
        num_media_items_added (int): The number of media items added.
        num_media_items_deleted (int): The number of media items deleted.
    """

    num_media_items_added: int
    num_media_items_deleted: int


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
        gphotos_uploader: GPhotosMediaItemUploader,
        diffs_assigner: DiffsAssigner,
    ):
        self.__config = config
        self.__albums_repo = albums_repo
        self.__media_items_repo = media_items_repo
        self.__gphotos_uploader = gphotos_uploader
        self.__diffs_assigner = diffs_assigner

    def backup(self, diffs: list[ProcessedDiff]) -> BackupResults:
        """Backs up a list of media items based on a list of diffs.

        Args:
            diffs (list[ProcessedDiff]): A list of processed diffs.

        Returns:
            BackupResults: A set of results from the backup.
        """
        # Step 1: Build a tree of albums with diffs on their edge nodes
        root_diffs_tree_node = self.__build_diffs_tree(diffs)
        logger.debug(f"Finished creating initial diff tree: {root_diffs_tree_node}")

        # Step 2: Create the missing photo albums in Mongo DB from the diffs tree
        # and attach the albums from database to the DiffTree
        self.__attach_albums_to_diff_tree(root_diffs_tree_node)
        logger.debug(f"Finished attaching albums to diff tree: {root_diffs_tree_node}")

        # Step 3: Determine which photo to add belongs to which Google Photos account
        diff_assignments = self.__diffs_assigner.get_diffs_assignments(diffs)
        logger.debug(f"Diff assignments: {diff_assignments}")

        # Step 4: Upload the photos to Google Photos
        upload_diff_to_gphotos_media_item_id = self.__upload_diffs_to_gphotos(
            diff_assignments
        )
        logger.debug(
            f"Added diffs to Google Photos: {upload_diff_to_gphotos_media_item_id}"
        )

        # Step 5: Add the uploaded photos to the database
        diff_to_uploaded_media_item: Dict[ProcessedDiff, MediaItem] = {}
        for diff, gphotos_media_item_id in upload_diff_to_gphotos_media_item_id.items():
            gphotos_client_id = diff_assignments[diff]
            create_media_item_request = CreateMediaItemRequest(
                file_name=diff.file_name,
                hash_code=None,
                location=diff.location,
                gphotos_client_id=gphotos_client_id,
                gphotos_media_item_id=gphotos_media_item_id,
            )

            media_item = self.__media_items_repo.create_media_item(
                create_media_item_request
            )
            diff_to_uploaded_media_item[diff] = media_item
        logger.debug(f"Added diffs to the database: {diff_to_uploaded_media_item}")

        # Step 6: Go through the tree
        media_item_ids_to_delete = []
        queue = deque([root_diffs_tree_node])
        while len(queue) > 0:
            cur_diffs_tree_node = queue.popleft()
            cur_album = cast(Album, cur_diffs_tree_node.album)

            add_diffs = cur_diffs_tree_node.modifier_to_diffs.get("+", [])
            delete_diffs = cur_diffs_tree_node.modifier_to_diffs.get("-", [])

            # Step 6a: Find media items to delete
            deleted_file_names_set = set([diff.file_name for diff in delete_diffs])
            deleted_media_item_ids = set([])
            for media_item_id in cur_album.media_item_ids:
                media_item = self.__media_items_repo.get_media_item_by_id(media_item_id)

                if media_item.file_name in deleted_file_names_set:
                    media_item_ids_to_delete.append(media_item.id)
                    deleted_media_item_ids.add(media_item.id)

            # Step 6b: Find the media items to add to the album
            added_media_item_ids = []
            for add_diff in add_diffs:
                media_item_id = diff_to_uploaded_media_item[add_diff].id
                added_media_item_ids.append(media_item_id)

            # Step 6c: Get a new list of media item ids for the album
            new_media_item_ids: list[MediaItemId] = []
            for media_item_id in cur_album.media_item_ids:
                if media_item_id not in deleted_media_item_ids:
                    new_media_item_ids.append(media_item_id)
            new_media_item_ids += added_media_item_ids

            # Step 6d: Update the album with the new list of media item ids
            if len(deleted_media_item_ids) > 0 or len(added_media_item_ids) > 0:
                self.__albums_repo.update_album(
                    cur_album.id,
                    UpdatedAlbumFields(new_media_item_ids=new_media_item_ids),
                )

            for child_diff_tree_node in cur_diffs_tree_node.child_nodes:
                queue.append(child_diff_tree_node)

        # Step 7: Delete the media items marked for deletion
        self.__media_items_repo.delete_many_media_items(media_item_ids_to_delete)

        # Step 8: Return the results of the backup
        return BackupResults(
            num_media_items_added=len(diff_to_uploaded_media_item.keys()),
            num_media_items_deleted=len(media_item_ids_to_delete),
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

    def __attach_albums_to_diff_tree(self, diff_tree: DiffsTreeNode):
        """
        Attaches albums from MongoDB to the diff tree
        If there are any albums missing in MongoDB, it will create it.

        Args:
            diff_tree (DiffsTreeNode): The root of the diff tree.
        """
        root_album_id = self.__config.get_root_album_id()
        root_album = self.__albums_repo.get_album_by_id(root_album_id)
        queue = deque([(diff_tree, root_album)])

        while len(queue) > 0:
            cur_diffs_tree_node, cur_album = queue.popleft()
            cur_diffs_tree_node.album = cur_album

            child_album_name_to_album: Dict[str, Album] = {}
            for child_album_id in cur_album.child_album_ids:
                child_album = self.__albums_repo.get_album_by_id(child_album_id)

                child_album_name_to_album[cast(str, child_album.name)] = child_album

            created_child_album_ids = []
            for child_diff_node in cur_diffs_tree_node.child_nodes:
                if child_diff_node.album_name not in child_album_name_to_album:
                    new_album = self.__albums_repo.create_album(
                        album_name=child_diff_node.album_name,
                        parent_album_id=cur_album.id,
                        child_album_ids=[],
                        media_item_ids=[],
                    )
                    child_album_name_to_album[child_diff_node.album_name] = new_album
                    created_child_album_ids.append(new_album.id)

                child_album = child_album_name_to_album[child_diff_node.album_name]
                queue.append((child_diff_node, child_album))

            if len(created_child_album_ids) > 0:
                new_child_album_ids = (
                    cur_album.child_album_ids + created_child_album_ids
                )
                self.__albums_repo.update_album(
                    album_id=cur_album.id,
                    updated_album_fields=UpdatedAlbumFields(
                        new_child_album_ids=new_child_album_ids
                    ),
                )

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
            dict[ProcessedDiff, str]: A map of diffs to their media item IDs on Google Photos.
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
        upload_diff_to_gphotos_media_item_id = {
            item[0]: gphotos_media_item_id
            for item, gphotos_media_item_id in zip(
                diff_assignments_items, gphotos_media_item_ids
            )
        }

        return upload_diff_to_gphotos_media_item_id
