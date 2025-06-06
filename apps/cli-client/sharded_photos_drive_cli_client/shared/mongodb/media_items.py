from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from bson.objectid import ObjectId

from sharded_photos_drive_cli_client.shared.mongodb.media_item_id import MediaItemId
from sharded_photos_drive_cli_client.shared.mongodb.album_id import AlbumId


@dataclass(frozen=True)
class GpsLocation:
    """
    Represents a GPS location.

    Attributes:
        latitude (float): The latitude in degrees.
        longitude (float): The longitude in degrees.
    """

    latitude: float
    longitude: float


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
