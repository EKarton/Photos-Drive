from dataclasses import dataclass

from bson.objectid import ObjectId

from .media_items import MediaItemId


@dataclass(frozen=True)
class AlbumId:
    """
    Represents the ID of a album in MongoDB.
    Since albums are distributed across different MongoDB clients, it consists of the
    MongoDB client ID and the object ID.

    Attributes:
        client_id (ObjectId): The ID of the Mongo DB client that it is saved under.
        object_id (ObjectId): The object ID of the document
    """

    client_id: ObjectId
    object_id: ObjectId


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
        media_item_ids (list[MediaItemId]): The IDs of media items that is under this
            album.
    """

    id: AlbumId
    name: str | None
    parent_album_id: AlbumId | None
    child_album_ids: list[AlbumId]
    media_item_ids: list[MediaItemId]
