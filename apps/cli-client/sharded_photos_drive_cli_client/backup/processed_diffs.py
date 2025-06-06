from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import logging
import os
from typing import Optional, cast
from exiftool import ExifToolHelper  # type: ignore

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
    width: int
    height: int
    date_taken: datetime


class DiffsProcessor:
    def process_raw_diffs(self, diffs: list[Diff]) -> list[ProcessedDiff]:
        """Processes raw diffs into processed diffs, parsing their metadata."""

        def process_diff(diff):
            if diff.modifier not in ("+", "-"):
                raise ValueError(f"Modifier {diff.modifier} in {diff} not allowed.")

            if diff.modifier == "+" and not os.path.exists(diff.file_path):
                raise ValueError(f"File {diff.file_path} does not exist.")

            return ProcessedDiff(
                modifier=diff.modifier,
                file_path=diff.file_path,
                file_hash=self.__compute_file_hash(diff),
                album_name=self.__get_album_name(diff),
                file_name=self.__get_file_name(diff),
                file_size=self.__get_file_size_in_bytes(diff),
                location=None,  # Placeholder; will be updated later
                width=0,  # Placeholder; will be updated later
                height=0,  # Placeholder; will be updated later
                date_taken=datetime.now(),  # Placeholder; will be updated later
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
                cast(ProcessedDiff, processed_diff), location=exif_metadatas[i].location
            )

        return cast(list[ProcessedDiff], processed_diffs)

    def __get_exif_metadatas(self, diffs: list[Diff]) -> list[ExtractedExifMetadata]:
        metadatas = [ExtractedExifMetadata(None, 0, 0, datetime.now())] * len(diffs)

        missing_metadata_and_idx: list[tuple[Diff, int]] = []
        for i, diff in enumerate(diffs):
            if diff.modifier == "-":
                continue

            if diff.location and diff.width and diff.height and diff.date_taken:
                new_metadata = ExtractedExifMetadata(
                    diff.location, diff.width, diff.height, diff.date_taken
                )
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
                    "EXIF:ImageWidth",  # for images
                    "EXIF:ImageHeight",
                    "Composite:ImageSize",  # fallback for image size (as WxH string)
                    "Composite:Rotation",  # adjust dimensions for rotated videos
                    "QuickTime:ImageWidth",  # for videos
                    "QuickTime:ImageHeight",
                ],
            )

            for i, raw_metadata in enumerate(raw_metadatas):
                latitude = raw_metadata.get("Composite:GPSLatitude")
                longitude = raw_metadata.get("Composite:GPSLongitude")

                location = None
                if latitude and longitude:
                    location = GpsLocation(
                        latitude=cast(int, latitude), longitude=cast(int, longitude)
                    )

                date_str = raw_metadata.get(
                    "EXIF:DateTimeOriginal"
                ) or raw_metadata.get("QuickTime:CreateDate")
                date_taken = datetime.now()
                if date_str:
                    try:
                        date_taken = datetime.strptime(
                            date_str, "%Y:%m:%d %H:%M:%S"
                        ).replace(tzinfo=timezone.utc)
                    except ValueError:
                        logger.debug('Failed to parse date taken. Attempt 2')
                        try:
                            # Try ISO format fallback
                            date_taken = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        except Exception:
                            logger.debug('Failed to parse date taken. No more attempts')
                            pass

                width = raw_metadata.get("QuickTime:ImageWidth") or raw_metadata.get(
                    "EXIF:ImageWidth"
                )
                height = raw_metadata.get("QuickTime:ImageHeight") or raw_metadata.get(
                    "EXIF:ImageHeight"
                )

                if not width or not height:
                    size_str = raw_metadata.get(
                        "Composite:ImageSize"
                    )  # e.g., "1920x1080"
                    if isinstance(size_str, str) and "x" in size_str:
                        w_str, h_str = size_str.split("x")
                        width = int(w_str)
                        height = int(h_str)
                    else:
                        width = 0
                        height = 0

                metadatas[missing_metadata_and_idx[i][1]] = ExtractedExifMetadata(
                    location, width, height, date_taken
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
