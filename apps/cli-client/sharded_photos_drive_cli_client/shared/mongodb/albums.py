from dataclasses import dataclass


from .album_id import AlbumId


@dataclass(frozen=True)
class Album:
    """
    Represents an album in MongoDB.

    Attributes:
        id (AlbumId): The album ID.
        name (str | None): The name of the album. If it is None, it will be considered
            a root album.
        parent_album_id (AlbumId | None): The parent album ID. If it is None, it does
            not have a parent album.
        child_album_ids (list[AlbumId]): The IDs of albums that is under this album.
    """

    id: AlbumId
    name: str | None
    parent_album_id: AlbumId | None
    child_album_ids: list[AlbumId]
