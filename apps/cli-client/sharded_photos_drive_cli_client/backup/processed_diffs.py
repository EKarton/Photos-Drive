from dataclasses import dataclass
import os
from typing import cast
from exiftool import ExifToolHelper  # type: ignore

from ..shared.hashes.xxhash import compute_file_hash
from ..shared.mongodb.media_items import GpsLocation

from .diffs import Diff


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
    """

    modifier: str
    file_path: str
    album_name: str
    file_name: str
    file_size: int
    file_hash: bytes
    location: GpsLocation | None


class DiffsProcessor:
    def process_raw_diffs(self, diffs: list[Diff]) -> list[ProcessedDiff]:
        """Processes raw diffs into processed diffs, parsing their metadata."""

        processed_diffs = []

        # Verify diffs
        for diff in diffs:
            if diff.modifier != "+" and diff.modifier != "-":
                raise ValueError(f"Modifier {diff.modifier} in {diff} not allowed.")

            if diff.modifier == "+" and not os.path.exists(diff.file_path):
                raise ValueError(f"File {diff.file_path} does not exist.")

        # Get locations from all diffs
        locations = self.__get_locations(diffs)

        # Process diffs
        for i, diff in enumerate(diffs):
            processed_diffs.append(
                ProcessedDiff(
                    modifier=diff.modifier,
                    file_path=diff.file_path,
                    file_hash=compute_file_hash(diff.file_path),
                    album_name=self.__get_album_name(diff),
                    file_name=self.__get_file_name(diff),
                    file_size=self.__get_file_size_in_bytes(diff),
                    location=locations[i],
                )
            )

        return processed_diffs

    def __get_locations(self, diffs: list[Diff]) -> list[GpsLocation | None]:
        locations: list[GpsLocation | None] = [None] * len(diffs)

        missing_locations_and_idx: list[tuple[Diff, int]] = []
        for i, diff in enumerate(diffs):
            if diff.modifier == "-":
                continue

            if diff.location:
                locations[i] = diff.location
                continue

            missing_locations_and_idx.append((diff, i))

        if len(missing_locations_and_idx) == 0:
            return locations

        with ExifToolHelper() as exiftool_client:
            file_paths = [d[0].file_path for d in missing_locations_and_idx]
            metadatas = exiftool_client.get_tags(
                file_paths, ['gpslatitude', 'gpslongitude']
            )

            for i, metadata in enumerate(metadatas):
                latitude = metadata.get("Composite:GPSLatitude")
                longitude = metadata.get("Composite:GPSLongitude")

                location = None
                if latitude and longitude:
                    location = GpsLocation(
                        latitude=cast(int, latitude), longitude=cast(int, longitude)
                    )

                locations[missing_locations_and_idx[i][1]] = location

        return locations

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
