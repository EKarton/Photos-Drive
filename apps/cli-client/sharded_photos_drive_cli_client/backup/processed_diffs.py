from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from datetime import datetime
import logging
import os
from typing import Optional, cast
from exiftool import ExifToolHelper

from ..shared.dimensions.cv2_video_dimensions import (
    get_width_height_of_video,
)
from ..shared.dimensions.pillow_image_dimensions import (
    get_width_height_of_image,
)
from ..shared.gphotos.valid_file_extensions import (
    IMAGE_FILE_EXTENSIONS,
)

from ..shared.hashes.xxhash import compute_file_hash
from ..shared.mongodb.media_items import GpsLocation

from .diffs import Diff

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessedDiff:
    """
    Represents the diff of a media item with processed metadata.
    A media item represents either a video or image.

    Attributes:
        modifier (str): The modifier.
        file_path (str): The file path.
        album_name (str): The album name.
        file_name (str): The file name
        file_size (int): The file size, in the number of bytes.
        file_hash (bytes): The file hash, in bytes.
        location (GpsLocation | None): The GPS latitude if it exists; else None.
        width: (int): The width of the image / video.
        height (int): The height of the image / video.
        date_taken (datetime): The date and time for when the image / video was taken.
    """

    modifier: str
    file_path: str
    album_name: str
    file_name: str
    file_size: int
    file_hash: bytes
    location: GpsLocation | None
    width: int
    height: int
    date_taken: datetime


@dataclass(frozen=True)
class ExtractedExifMetadata:
    location: GpsLocation | None
    date_taken: datetime


class DiffsProcessor:
    def process_raw_diffs(self, diffs: list[Diff]) -> list[ProcessedDiff]:
        """Processes raw diffs into processed diffs, parsing their metadata."""

        def process_diff(diff: Diff) -> ProcessedDiff:
            if diff.modifier not in ("+", "-"):
                raise ValueError(f"Modifier {diff.modifier} in {diff} not allowed.")

            if diff.modifier == "+" and not os.path.exists(diff.file_path):
                raise ValueError(f"File {diff.file_path} does not exist.")

            width, height = self.__get_width_height(diff)

            return ProcessedDiff(
                modifier=diff.modifier,
                file_path=diff.file_path,
                file_hash=self.__compute_file_hash(diff),
                album_name=self.__get_album_name(diff),
                file_name=self.__get_file_name(diff),
                file_size=self.__get_file_size_in_bytes(diff),
                location=None,  # Placeholder; will be updated later
                width=width,
                height=height,
                date_taken=datetime(1970, 1, 1),  # Placeholder; will be updated later
            )

        processed_diffs: list[Optional[ProcessedDiff]] = [None] * len(diffs)
        with ThreadPoolExecutor() as executor:
            future_to_idx = {
                executor.submit(process_diff, diff): i for i, diff in enumerate(diffs)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                processed_diffs[idx] = future.result()

        # Get exif metadatas from all diffs
        exif_metadatas = self.__get_exif_metadatas(diffs)

        # Update locations in processed diffs
        for i, processed_diff in enumerate(processed_diffs):
            processed_diffs[i] = replace(
                cast(ProcessedDiff, processed_diff),
                location=exif_metadatas[i].location,
                date_taken=exif_metadatas[i].date_taken,
            )

        return cast(list[ProcessedDiff], processed_diffs)

    def __get_exif_metadatas(self, diffs: list[Diff]) -> list[ExtractedExifMetadata]:
        metadatas = [ExtractedExifMetadata(None, datetime(1970, 1, 1))] * len(diffs)

        missing_metadata_and_idx: list[tuple[Diff, int]] = []
        for i, diff in enumerate(diffs):
            if diff.modifier == "-":
                continue

            if diff.location and diff.date_taken:
                new_metadata = ExtractedExifMetadata(diff.location, diff.date_taken)
                metadatas[i] = new_metadata
                continue

            missing_metadata_and_idx.append((diff, i))

        if len(missing_metadata_and_idx) == 0:
            return metadatas

        with ExifToolHelper() as exiftool_client:
            file_paths = [d[0].file_path for d in missing_metadata_and_idx]
            raw_metadatas = exiftool_client.get_tags(
                file_paths,
                [
                    "Composite:GPSLatitude",
                    "Composite:GPSLongitude",
                    "EXIF:DateTimeOriginal",  # for images
                    "QuickTime:CreateDate",  # for videos (QuickTime/MP4)
                    "QuickTime:CreationDate",
                    'RIFF:DateTimeOriginal',  # for avi videos
                    'XMP-exif:DateTimeOriginal',  # for gifs
                    "TrackCreateDate",
                    "MediaCreateDate",
                ],
            )

            for i, raw_metadata in enumerate(raw_metadatas):
                location = diffs[i].location
                if location is None:
                    latitude = raw_metadata.get("Composite:GPSLatitude")
                    longitude = raw_metadata.get("Composite:GPSLongitude")
                    if latitude and longitude:
                        location = GpsLocation(
                            latitude=cast(int, latitude), longitude=cast(int, longitude)
                        )

                date_taken = diffs[i].date_taken
                if date_taken is None:
                    date_str = (
                        raw_metadata.get("EXIF:DateTimeOriginal")
                        or raw_metadata.get("QuickTime:CreateDate")
                        or raw_metadata.get('QuickTime:CreationDate')
                        or raw_metadata.get('RIFF:DateTimeOriginal')
                        or raw_metadata.get('XMP-exif:DateTimeOriginal')
                        or raw_metadata.get('TrackCreateDate')
                        or raw_metadata.get('MediaCreateDate')
                    )
                    if date_str:
                        date_taken = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    else:
                        date_taken = datetime(1970, 1, 1)

                metadatas[missing_metadata_and_idx[i][1]] = ExtractedExifMetadata(
                    location, date_taken
                )

        return metadatas

    def __compute_file_hash(self, diff: Diff) -> bytes:
        if diff.modifier == "-":
            return b'0'
        return compute_file_hash(diff.file_path)

    def __get_album_name(self, diff: Diff) -> str:
        if diff.album_name:
            return diff.album_name

        album_name = os.path.dirname(diff.file_path)

        # Remove the trailing dots / non-chars
        # (ex: ../../Photos/2010/Dog becomes Photos/2010/Dog)
        pos = -1
        for i, x in enumerate(album_name):
            if x.isalpha():
                pos = i
                break
        album_name = album_name[pos:]

        # Convert album names like Photos\2010\Dog to Photos/2010/Dog
        album_name = album_name.replace("\\", "/")

        return album_name

    def __get_file_name(self, diff: Diff) -> str:
        if diff.file_name:
            return diff.file_name

        return os.path.basename(diff.file_path)

    def __get_file_size_in_bytes(self, diff: Diff) -> int:
        if diff.modifier == "-":
            return 0

        if diff.file_size:
            return diff.file_size

        return os.path.getsize(diff.file_path)

    def __get_width_height(self, diff: Diff) -> tuple[int, int]:
        if diff.modifier == '-':
            return 0, 0

        if diff.file_path.lower().endswith(IMAGE_FILE_EXTENSIONS):
            return get_width_height_of_image(diff.file_path)
        else:
            return get_width_height_of_video(diff.file_path)
