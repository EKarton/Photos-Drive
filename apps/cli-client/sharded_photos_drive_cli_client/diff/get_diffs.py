from dataclasses import dataclass
from collections import deque
import logging
import os

from sharded_photos_drive_cli_client.shared.hashes.xxhash import compute_file_hash

from ..shared.gphotos.valid_file_extensions import MEDIA_ITEM_FILE_EXTENSIONS
from ..shared.config.config import Config
from ..shared.mongodb.albums import Album
from ..shared.mongodb.albums_repository import AlbumsRepository
from ..shared.mongodb.media_items_repository import MediaItemsRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RemoteFile:
    '''
    Represents a file in the Sharded Photos Drive system.

    Attributes:
        key: The unique key of the remote file. It should contain the
            remote file path + its hash code
        remote_relative_file_path: The relative file path stored in the Sharded
            Photos Drive system. This path should allow the CLI to delete the
            photo if needed.
    '''

    key: str
    remote_relative_file_path: str


@dataclass(frozen=True)
class LocalFile:
    '''
    Represents a file stored locally.

    Attributes:
        key: The unique key of the local file. It should contain the
            file path + its hash code
        local_relative_file_path: The relative file path pointing to a file saved
            locally. This path should allow the CLI to add photos to the system.
    '''

    key: str
    local_relative_file_path: str


@dataclass(frozen=True)
class DiffResults:
    missing_remote_files_in_local: list[RemoteFile]
    missing_local_files_in_remote: list[LocalFile]


class FolderSyncDiff:
    '''
    A class responsible for returning the difference between the contents of a
    folder and the contents in the Sharded Photos Drive.
    '''

    def __init__(
        self,
        config: Config,
        albums_repo: AlbumsRepository,
        media_items_repo: MediaItemsRepository,
    ):
        self.__config = config
        self.__albums_repo = albums_repo
        self.__media_items_repo = media_items_repo

    def get_diffs(self, local_dir_path: str, remote_dir_path: str) -> DiffResults:
        # Step 1: Go through the database and get all of its files
        remote_files = self.__get_remote_files(remote_dir_path)

        # Step 2: Go through the entire folder directory and build a tree
        local_files = self.__get_local_files(local_dir_path)

        logger.debug(f'Remote items: {remote_files}')
        logger.debug(f'Local items: {local_files}')

        # Step 3: Compare the trees
        return self.__get_diffs(remote_files, local_files)

    def __get_remote_files(self, remote_dir_path: str) -> list[RemoteFile]:
        found_files: list[RemoteFile] = []

        base_album = self.__find_leaf_album_in_dir_path(remote_dir_path)
        logger.debug(f"Base album: {base_album}")

        if not base_album:
            raise ValueError(
                f'Remote dir path {remote_dir_path} does not exist in the system'
            )

        base_album_id = base_album.id
        queue: deque = deque([(base_album_id, [])])

        while len(queue) > 0:
            album_id, prev_path = queue.popleft()
            album = self.__albums_repo.get_album_by_id(album_id)

            for media_item_id in album.media_item_ids:
                media_item = self.__media_items_repo.get_media_item_by_id(media_item_id)
                file_hash_str = (
                    media_item.file_hash.hex() if media_item.file_hash else ''
                )

                if album_id == base_album_id:
                    remote_file_path = f'{remote_dir_path}/{media_item.file_name}'
                    found_files.append(
                        RemoteFile(
                            key=f'{media_item.file_name}:{file_hash_str}',
                            remote_relative_file_path=remote_file_path,
                        )
                    )
                else:
                    remote_file_path = str.join(
                        '/', prev_path + [album.name, media_item.file_name]
                    )
                    remote_relative_file_path = f'{remote_dir_path}/{remote_file_path}'
                    found_files.append(
                        RemoteFile(
                            key=f'{remote_file_path}:{file_hash_str}',
                            remote_relative_file_path=remote_relative_file_path,
                        )
                    )

            for child_album_id in album.child_album_ids:
                if album_id == base_album_id:
                    queue.append((child_album_id, prev_path.copy()))
                else:
                    queue.append((child_album_id, prev_path + [album.name]))

        return found_files

    def __find_leaf_album_in_dir_path(self, remote_dir_path: str) -> Album | None:
        cur_album = self.__albums_repo.get_album_by_id(
            self.__config.get_root_album_id()
        )

        if len(remote_dir_path) == 0:
            return cur_album

        album_names_queue = deque(remote_dir_path.split('/'))

        while len(album_names_queue) > 0:
            album_name = album_names_queue.popleft()

            new_cur_album = None
            for child_album_id in cur_album.child_album_ids:
                child_album = self.__albums_repo.get_album_by_id(child_album_id)
                if child_album.name == album_name:
                    new_cur_album = child_album

            if not new_cur_album:
                return None

            cur_album = new_cur_album

        return cur_album

    def __get_local_files(self, dir_path: str) -> list[LocalFile]:
        found_files: list[LocalFile] = []
        base_album_path = os.path.relpath(dir_path)

        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.lower().endswith(MEDIA_ITEM_FILE_EXTENSIONS):
                    continue

                remote_album_path = os.path.relpath(root)
                if remote_album_path.startswith(base_album_path):
                    remote_album_path = remote_album_path[len(base_album_path) + 1 :]

                remote_file_path = os.path.join(remote_album_path, file).replace(
                    os.sep, "/"
                )
                local_file_path = os.path.join(
                    ".", os.path.relpath(os.path.join(root, file))
                )
                file_hash = compute_file_hash(local_file_path).hex()

                found_files.append(
                    LocalFile(
                        key=f'{remote_file_path}:{file_hash}',
                        local_relative_file_path=local_file_path,
                    )
                )

        return found_files

    def __get_diffs(
        self, remote_files: list[RemoteFile], local_files: list[LocalFile]
    ) -> DiffResults:
        remote_file_keys = set([f.key for f in remote_files])
        local_file_keys = set([f.key for f in local_files])

        return DiffResults(
            missing_remote_files_in_local=[
                obj for obj in remote_files if obj.key not in local_file_keys
            ],
            missing_local_files_in_remote=[
                obj for obj in local_files if obj.key not in remote_file_keys
            ],
        )
