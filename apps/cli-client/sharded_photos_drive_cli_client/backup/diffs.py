from dataclasses import dataclass
from datetime import datetime
from typing import Optional


from ..shared.mongodb.media_items import GpsLocation


@dataclass(frozen=True)
class Diff:
    """
    Represents the raw diff of a media item.
    A media item represents either a video or image.

    Attributes:
        modifier (str): The modifier (required).
        file_path (str): The file path (required).
        album_name (Optional[str]): The album name (optional). If not provided, it will
            be determined by the file_path.
        file_name (Optional[str]): The file name (optional). If not provided, it will be
            determined by the file_path.
        file_size (Optional[None]): The file size in bytes (optional). If not provided,
            it will be determined by reading its file.
        location (Optional[GpsLocation]): The GPS latitude (optional). If not provided,
            it will be determined by reading its exif data.
        width: (Optional[int]): The width of the image / video.
        height (Optional[int]): The height of the image / video.
        date_taken (Optional[datetime]): The date and time for when the image / video
            was taken.
    """

    modifier: str
    file_path: str
    album_name: Optional[str | None] = None
    file_name: Optional[str | None] = None
    file_size: Optional[int | None] = None
    location: Optional[GpsLocation | None] = None
    width: Optional[int] = None
    height: Optional[int] = None
    date_taken: Optional[datetime] = None
