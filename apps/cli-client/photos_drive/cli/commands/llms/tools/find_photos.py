from datetime import datetime
from typing import List, Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field

from photos_drive.cli.commands.llms.tools.media_item import (
    MediaItemModel,
    dataclass_to_pydantic_media_item,
)
from photos_drive.shared.metadata.gps_location import GpsLocation
from photos_drive.shared.metadata.media_items_repository import (
    FindMediaItemRequest,
    LocationRange,
    MediaItemsRepository,
)

DEFAULT_PROMPT = '''
Search your photo library by filtering photos based on date, location, and other
metadata. Use this tool to find photos by specifying date ranges or GPS coordinates
with radius.

Returns matching media items from your library.
'''


class FindPhotosInput(BaseModel):
    earliest_date_taken: str = Field(
        '',
        description=(
            "Filter to include only photos taken on or after this date "
            + "(format: YYYY-MM-DD). Leave empty to apply no lower date limit."
        ),
    )
    latest_date_taken: str = Field(
        '',
        description=(
            "Filter to include only photos taken on or before this date "
            + "(format: YYYY-MM-DD). Leave empty to apply no upper date limit."
        ),
    )
    within_geo_location: str = Field(
        '',
        description=(
            "GPS coordinate as a string in 'latitude,longitude' format. "
            "If provided alongside a positive 'within_geo_range', "
            "only photos taken within that radius (in meters) around this location "
            + "will be included. Leave empty to ignore location filtering."
        ),
    )
    within_geo_range: float = Field(
        0,
        description=(
            "Radius in meters to search around 'within_geo_location'. "
            "Must be greater than 0 to enable location-based filtering."
        ),
    )
    limit: Optional[int] = Field(
        50,
        description="Maximum number of photos to return.",
    )


class FindPhotosOutput(BaseModel):
    media_items: List[MediaItemModel] = Field(..., description="List of media items")


class FindPhotosTool(BaseTool):
    name: str = "FindPhotos"
    description: str = DEFAULT_PROMPT
    args_schema: Optional[ArgsSchema] = FindPhotosInput
    return_direct: bool = False

    media_items_repo: MediaItemsRepository = Field(..., exclude=True)

    def __init__(
        self,
        media_items_repo: MediaItemsRepository,
    ):
        super().__init__(media_items_repo=media_items_repo)

    def _run(
        self,
        earliest_date_taken: str = '',
        latest_date_taken: str = '',
        within_geo_location: str = '',
        within_geo_radius: float = 0,
        limit: int = 50,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> FindPhotosOutput:
        earliest_date_obj = None
        if earliest_date_taken != '':
            earliest_date_obj = datetime.strptime(earliest_date_taken, "%Y-%m-%d")

        latest_date_obj = None
        if latest_date_taken != '':
            latest_date_obj = datetime.strptime(latest_date_taken, "%Y-%m-%d")

        within_location_obj = None
        if within_geo_location and within_geo_radius > 0:
            within_geo_location_parts = within_geo_location.split(',')
            within_location_obj = LocationRange(
                location=GpsLocation(
                    latitude=int(within_geo_location_parts[0]),
                    longitude=int(within_geo_location_parts[1]),
                ),
                radius=within_geo_radius,
            )

        media_items = self.media_items_repo.find_media_items(
            FindMediaItemRequest(
                earliest_date_taken=earliest_date_obj,
                latest_date_taken=latest_date_obj,
                location_range=within_location_obj,
                limit=limit,
            )
        )

        return FindPhotosOutput(
            media_items=[
                dataclass_to_pydantic_media_item(media_item)
                for media_item in media_items
            ]
        )

    async def _arun(
        self,
        earliest_date_taken: str = '',
        latest_date_taken: str = '',
        within_geo_location: str = '',
        within_geo_radius: float = 0,
        limit: int = 50,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> FindPhotosOutput:
        """Use the tool asynchronously."""
        return self._run(
            earliest_date_taken,
            latest_date_taken,
            within_geo_location,
            within_geo_radius,
            limit,
            run_manager=run_manager.get_sync() if run_manager else None,
        )
