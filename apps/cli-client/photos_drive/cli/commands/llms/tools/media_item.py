from typing import Optional

from pydantic import BaseModel, Field

from photos_drive.shared.metadata import album_id
from photos_drive.shared.metadata.gps_location import GpsLocation
from photos_drive.shared.metadata.media_item_id import media_item_id_to_string
from photos_drive.shared.metadata.media_items import MediaItem


class GpsLocationModel(BaseModel):
    '''Represents a Gps location for LLM model'''

    latitude: float = Field(..., description="Latitude in degrees")
    longitude: float = Field(..., description="Longitude in degrees")

    class Config:
        schema_extra = {"example": {"latitude": 37.7749, "longitude": -122.4194}}


class MediaItemModel(BaseModel):
    '''Represents a media item for LLM model'''

    id: str = Field(..., description="ID of this media item")
    file_name: str = Field(..., description="File name of the media item")
    location: Optional[GpsLocationModel] = Field(
        None, description="GPS location if available"
    )
    gphotos_client_id: str = Field(..., description="Google Photos client ID")
    gphotos_media_item_id: str = Field(..., description="Google Photos media item ID")
    album_id: str = Field(..., description="Album ID that this media item belongs to")
    width: int = Field(..., description="Width of image/video in pixels")
    height: int = Field(..., description="Height of image/video in pixels")
    date_taken: str = Field(..., description="Timestamp when the image/video was taken")

    class Config:
        schema_extra = {
            "example": {
                "id": "client123:object456",
                "file_name": "photo1.jpg",
                "location": {"latitude": 37.7749, "longitude": -122.4194},
                "gphotos_client_id": "client123",
                "gphotos_media_item_id": "media789",
                "album_id": "album101112",
                "width": 4000,
                "height": 3000,
                "date_taken": "2023-07-01T15:30:00Z",
            }
        }


def dataclass_to_pydantic_media_item(media_item_dc: MediaItem) -> MediaItemModel:
    return MediaItemModel(
        id=media_item_id_to_string(media_item_dc.id),
        file_name=media_item_dc.file_name,
        location=(
            dataclass_to_pydantic_gps_location(media_item_dc.location)
            if media_item_dc.location
            else None
        ),
        gphotos_client_id=str(media_item_dc.gphotos_client_id),
        gphotos_media_item_id=str(media_item_dc.gphotos_media_item_id),
        album_id=album_id.album_id_to_string(media_item_dc.album_id),
        width=media_item_dc.width,
        height=media_item_dc.height,
        date_taken=str(media_item_dc.date_taken),
    )


def dataclass_to_pydantic_gps_location(
    gps_location_dc: GpsLocation,
) -> GpsLocationModel:
    return GpsLocationModel(
        latitude=gps_location_dc.latitude, longitude=gps_location_dc.longitude
    )
