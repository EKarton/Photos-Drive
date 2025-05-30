from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from collections import deque
import logging
import os
from typing import cast

from ..shared.mongodb.album_id import AlbumId
from ..shared.hashes.xxhash import compute_file_hash
from ..shared.gphotos.valid_file_extensions import MEDIA_ITEM_FILE_EXTENSIONS
from ..shared.config.config import Config
from ..shared.mongodb.albums import Album
from ..shared.mongodb.albums_repository import AlbumsRepository
from ..shared.mongodb.media_items_repository import (
    FindMediaItemRequest,
    MediaItemsRepository,
)

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
        logger.debug(f'Remote items: {remote_files}')

        # Step 2: Go through the entire folder directory and build a tree
        local_files = self.__get_local_files(local_dir_path)
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

        def process_album(
            album_id: AlbumId, prev_path: list[str]
        ) -> tuple[list[RemoteFile], list[tuple[AlbumId, list[str]]]]:
            '''
            This helper processes one album and returns:
            - the RemoteFile objects for its media items,
            - a list of child album tuples (child_album_id, new_prev_path)
            '''

            album = self.__albums_repo.get_album_by_id(album_id)
            local_found_files: list[RemoteFile] = []

            # Process media items for this album.
            for media_item in self.__media_items_repo.find_media_items(
                FindMediaItemRequest(album_id=album_id)
            ):
                file_hash_str = (
                    media_item.file_hash.hex() if media_item.file_hash else ''
                )

                if album_id == base_album_id:
                    remote_file_path = f'{remote_dir_path}/{media_item.file_name}'
                    local_found_files.append(
                        RemoteFile(
                            key=f'{media_item.file_name}:{file_hash_str}',
                            remote_relative_file_path=remote_file_path,
                        )
                    )
                else:
                    # Build the relative path
                    remote_file_path = '/'.join(
                        prev_path + [cast(str, album.name), media_item.file_name]
                    )
                    remote_relative_file_path = f'{remote_dir_path}/{remote_file_path}'
                    local_found_files.append(
                        RemoteFile(
                            key=f'{remote_file_path}:{file_hash_str}',
                            remote_relative_file_path=remote_relative_file_path,
                        )
                    )

            # Build new tuples for child albums.
            child_album_tuples = []
            for child_album_id in album.child_album_ids:
                if album_id == base_album_id:
                    child_album_tuples.append((child_album_id, prev_path.copy()))
                else:
                    child_album_tuples.append(
                        (child_album_id, prev_path + [cast(str, album.name)])
                    )

            return local_found_files, child_album_tuples

        # Perform parallel BFS
        with ThreadPoolExecutor() as executor:
            cur_level: list[tuple[AlbumId, list[str]]] = [(base_album_id, [])]

            while len(cur_level) > 0:
                futures = [
                    executor.submit(process_album, cur_album_id, prev_path)
                    for cur_album_id, prev_path in cur_level
                ]

                next_level: list[tuple[AlbumId, list[str]]] = []
                for future in as_completed(futures):
                    local_found_files, child_album_tuples = future.result()

                    found_files += local_found_files
                    next_level += child_album_tuples

                cur_level = next_level

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
        def process_file(base_album_path: str, root: str, file: str) -> LocalFile:
            """
            Processes a single file: computes its relative path, computes the file hash,
            and returns a LocalFile instance.
            """
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

            return LocalFile(
                key=f'{remote_file_path}:{file_hash}',
                local_relative_file_path=local_file_path,
            )

        found_files: list[LocalFile] = []
        base_album_path = os.path.relpath(dir_path)
        tasks = []

        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.lower().endswith(MEDIA_ITEM_FILE_EXTENSIONS):
                    continue

                tasks.append((root, file))

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(process_file, base_album_path, root, file)
                for root, file in tasks
            ]
            for future in as_completed(futures):
                found_files.append(future.result())

        return found_files

    def __get_diffs(
        self, remote_files: list[RemoteFile], local_files: list[LocalFile]
    ) -> DiffResults:
        # Build the key sets concurrently.
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both map creations concurrently.
            future_remote_keys = executor.submit(lambda: {f.key for f in remote_files})
            future_local_keys = executor.submit(lambda: {f.key for f in local_files})
            remote_file_keys = future_remote_keys.result()
            local_file_keys = future_local_keys.result()

            # Define functions for the filtering tasks.
            def filter_missing_remote():
                return [obj for obj in remote_files if obj.key not in local_file_keys]

            def filter_missing_local():
                return [obj for obj in local_files if obj.key not in remote_file_keys]

            # Submit both filtering tasks concurrently.
            future_missing_remote = executor.submit(filter_missing_remote)
            future_missing_local = executor.submit(filter_missing_local)

            missing_remote_files_in_local = future_missing_remote.result()
            logger.debug('Obtained missing items in remote')

            missing_local_files_in_remote = future_missing_local.result()
            logger.debug('Obtained missing items in local')

        return DiffResults(
            missing_remote_files_in_local=missing_remote_files_in_local,
            missing_local_files_in_remote=missing_local_files_in_remote,
        )
