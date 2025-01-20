from typing import cast
from sharded_photos_drive_cli_client.shared.mongodb.albums import AlbumId
from .albums_repository import AlbumsRepository, UpdatedAlbumFields


class AlbumsPruner:
    '''A class responsible for pruning albums in the albums tree.'''

    def __init__(self, root_album_id: AlbumId, albums_repo: AlbumsRepository):
        self.__albums_repo = albums_repo
        self.__root_album_id = root_album_id

    def prune_album(self, album_id: AlbumId) -> int:
        '''
        Prunes albums upwards in the albums tree.
        For instance, if we have this album structure:

        Archives
        └── Photos
            ├── random.jpg
            └── 2011
                └── Wallpapers

        running AlbumsPruner.prune_album() on Wallpapers will delete Wallpapers and
        2011, and make the albums tree become:

        Archives
        └── Photos
            └── random.jpg

        Args:
            album_id (AlbumId): The starting node.

        Returns:
            int: The number of albums that have been deleted.
        '''
        albums_to_delete: list[AlbumId] = []
        prev_album_id_deleted = None
        cur_album_id = album_id
        cur_album = self.__albums_repo.get_album_by_id(cur_album_id)

        while True:
            cur_album = self.__albums_repo.get_album_by_id(cur_album_id)
            if len(cur_album.child_album_ids) > 1:
                break

            if len(cur_album.media_item_ids) > 0:
                break

            if cur_album.id == self.__root_album_id:
                break

            parent_album_id = cast(AlbumId, cur_album.parent_album_id)
            albums_to_delete.append(cur_album_id)

            prev_album_id_deleted = cur_album_id
            cur_album_id = parent_album_id
            cur_album = self.__albums_repo.get_album_by_id(parent_album_id)

        new_child_album_ids = [
            child_album_id
            for child_album_id in cur_album.child_album_ids
            if child_album_id != prev_album_id_deleted
        ]

        if new_child_album_ids != cur_album.child_album_ids:
            self.__albums_repo.update_album(
                cur_album_id,
                UpdatedAlbumFields(new_child_album_ids=new_child_album_ids),
            )

        self.__albums_repo.delete_many_albums(albums_to_delete)

        return len(albums_to_delete)
