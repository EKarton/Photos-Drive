from collections import deque
from typing import cast

from ..shared.mongodb.albums import AlbumId
from ..shared.hashes.xxhash import compute_file_hash
from ..shared.config.config import Config
from ..shared.mongodb.albums_repository import AlbumsRepositoryImpl
from ..shared.mongodb.clients_repository import MongoDbClientsRepository
from ..shared.mongodb.media_items_repository import (
    MediaItemsRepositoryImpl,
    UpdateMediaItemRequest,
)


class AddFileHashesHandler:
    def run(self, config: Config):
        mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_clients_repo)
        media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)

        update_media_item_requests: list[UpdateMediaItemRequest] = []
        root_album_id = config.get_root_album_id()
        albums_queue: deque[tuple[AlbumId, list[str]]] = deque([(root_album_id, [])])
        while len(albums_queue) > 0:
            album_id, prev_albums_path = albums_queue.popleft()
            album = albums_repo.get_album_by_id(album_id)

            for child_album_id in album.child_album_ids:
                if album_id == root_album_id:
                    albums_queue.append((child_album_id, prev_albums_path + ['.']))
                else:
                    albums_queue.append(
                        (child_album_id, prev_albums_path + [cast(str, album.name)])
                    )

            for media_item_id in album.media_item_ids:
                media_item = media_items_repo.get_media_item_by_id(media_item_id)
                if album_id == root_album_id:
                    file_path = '/'.join(prev_albums_path + [media_item.file_name])
                else:
                    file_path = '/'.join(
                        prev_albums_path + [cast(str, album.name), media_item.file_name]
                    )
                file_hash = compute_file_hash(file_path)

                print(f'{file_path}: {file_hash.hex()}')

                update_media_item_requests.append(
                    UpdateMediaItemRequest(media_item_id, new_file_hash=file_hash)
                )

        media_items_repo.update_many_media_items(update_media_item_requests)
