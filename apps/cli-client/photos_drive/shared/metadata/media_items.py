from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bson.objectid import ObjectId

from photos_drive.shared.llm.vector_stores.base_vector_store import MediaItemEmbeddingId
from photos_drive.shared.metadata.album_id import AlbumId
from photos_drive.shared.metadata.gps_location import GpsLocation
from photos_drive.shared.metadata.media_item_id import MediaItemId


@dataclass(frozen=True)
class MediaItem:
    """
    Represents a media item in MongoDB.
    A media item represents either an image or a video.

    Attributes:
        id (MediaItemId): The ID of the media item.
        file_name (str): The name of the media item.
        file_hash (bytes): The hash code of the media item, in bytes.
        location (Optional[GpsLocation]): The gps location of the media item, if it
            exists. Else none.
        gphotos_client_id (ObjectId): The Google Photos client ID that it is saved
            under.
        gphotos_media_item_id (str): The media item ID that is saved in Google Photos.
        album_id (AlbumId): The album ID that it belongs to.
        width: (int): The width of the image / video.
        height (int): The height of the image / video.
        date_taken (datetime): The date and time for when the image / video was taken.
        embedding_id (Optional[MediaItemEmbeddingId]): The ID referring to its embedding
            in the vector store.
    """

    id: MediaItemId
    file_name: str
    file_hash: bytes
    location: Optional[GpsLocation]
    gphotos_client_id: ObjectId
    gphotos_media_item_id: str
    album_id: AlbumId
    width: int
    height: int
    date_taken: datetime
    embedding_id: Optional[MediaItemEmbeddingId]
