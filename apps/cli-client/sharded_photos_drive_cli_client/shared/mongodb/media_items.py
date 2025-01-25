from dataclasses import dataclass
from typing import Optional

from bson.objectid import ObjectId


@dataclass(frozen=True)
class MediaItemId:
    """
    Represents the ID of a media item in MongoDB.
    Since media items are distributed across different MongoDB clients, it consists of
    the MongoDB client ID and the object ID.

    Attributes:
        client_id (ObjectId): The ID of the Mongo DB client that it is saved under.
        object_id (ObjectId): The object ID of the document
    """

    client_id: ObjectId
    object_id: ObjectId


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
    """

    id: MediaItemId
    file_name: str
    file_hash: bytes
    location: Optional[GpsLocation]
    gphotos_client_id: ObjectId
    gphotos_media_item_id: str
