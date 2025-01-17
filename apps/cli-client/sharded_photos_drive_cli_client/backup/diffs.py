from dataclasses import dataclass
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
        album_name (str | None): The album name (optional). If not provided, it will be
            determined by the file_path.
        file_name (str | None): The file name (optional). If not provided, it will be
            determined by the file_path.
        file_size (int | None): The file size in bytes (optional). If not provided, it
            will be determined by reading its file.
        location (GpsLocation | None): The GPS latitude (optional). If not provided, it
            will be determined by reading its exif data.

    """

    modifier: str
    file_path: str
    album_name: Optional[str | None] = None
    file_name: Optional[str | None] = None
    file_size: Optional[int | None] = None
    location: Optional[GpsLocation | None] = None
