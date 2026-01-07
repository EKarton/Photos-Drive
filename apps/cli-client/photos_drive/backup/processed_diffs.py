from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from datetime import datetime
import logging
import os
from typing import Optional, Tuple, cast

from PIL import Image, ImageFile
from exiftool import ExifToolHelper
import magic
import numpy as np
from tqdm import tqdm

from photos_drive.backup.diffs import Diff, Modifier
from photos_drive.shared.llm.models.image_captions import ImageCaptions
from photos_drive.shared.llm.models.image_embeddings import ImageEmbeddings
from photos_drive.shared.metadata.gps_location import GpsLocation
from photos_drive.shared.utils.dimensions.cv2_video_dimensions import (
    get_width_height_of_video,
)
from photos_drive.shared.utils.dimensions.pillow_image_dimensions import (
    get_width_height_of_image,
)
from photos_drive.shared.utils.hashes.xxhash import compute_file_hash
from photos_drive.shared.utils.mime_type.utils import is_image

logger = logging.getLogger(__name__)

Image.MAX_IMAGE_PIXELS = None
ImageFile.LOAD_TRUNCATED_IMAGES = True

DEFAULT_DATE_TIME = datetime(1970, 1, 1)

EMPTY_CAPTIONS = ''
EMPTY_EMBEDDING = np.empty((1,), dtype=np.float32)


@dataclass(frozen=True)
class ProcessedDiff:
    """
    Represents the diff of a media item with processed metadata.
    A media item represents either a video or image.

    Attributes:
        modifier (Modifier): The modifier.
        file_path (str): The file path.
        album_name (str): The album name.
        file_name (str): The file name
        file_size (int): The file size, in the number of bytes.
        file_hash (bytes): The file hash, in bytes.
        location (GpsLocation | None): The GPS latitude if it exists; else None.
        width: (int): The width of the image / video.
        height (int): The height of the image / video.
        date_taken (datetime): The date and time for when the image / video was taken.
        mime_type (str): The mime type of this image / video.
        captions (str): The captions for this image / video.
        embedding (np.ndarray): The embedding of this image / video.
    """

    modifier: Modifier
    file_path: str
    album_name: str
    file_name: str
    file_size: int
    file_hash: bytes
    location: GpsLocation | None
    width: int
    height: int
    date_taken: datetime
    mime_type: str
    captions: str
    embedding: np.ndarray = field(compare=False, hash=False)


@dataclass(frozen=True)
class ExtractedExifMetadata:
    location: GpsLocation | None
    date_taken: datetime


class DiffsProcessor:
    def __init__(
        self,
        image_embedder: ImageEmbeddings,
        image_captions: ImageCaptions,
        embedder_batch_size=16,
        captions_batch_size=16,
    ):
        '''
        Constructs an instance of {@code DiffsProcessor}

        Args:
            - image_embedder (ImageEmbeddings):
                The image embedder
            - image_captions (ImageCaptions)
                The image captions generator
            - embedder_batch_size (int):
                The number of images / videos to get its embeddings in parallel.
            captions_batch_size (int):
                The number of images / videos to get its captions in parallel.
        '''
        self.image_embedder = image_embedder
        self.image_captions = image_captions
        self.embedder_batch_size = embedder_batch_size
        self.captions_batch_size = captions_batch_size

    def process_raw_diffs(self, diffs: list[Diff]) -> list[ProcessedDiff]:
        """
        Processes raw diffs into processed diffs, parsing their metadata.

        Args:
            - diffs (list[Diff]): A list of diffs

        Returns:
            list[ProcessedDiff]: A list of processed diffs

        """
        processed_diffs = self.__get_basic_processed_diffs(diffs)
        processed_diffs = self.__populate_processed_diffs_with_exif_metadata(
            diffs, processed_diffs
        )
        processed_diffs = self.__populate_processed_diffs_with_captions(
            diffs, processed_diffs
        )
        processed_diffs = self.__populate_processed_diffs_with_embeddings(
            diffs, processed_diffs
        )

        return processed_diffs

    def __get_basic_processed_diffs(self, diffs: list[Diff]) -> list[ProcessedDiff]:
        def process_diff(diff: Diff) -> ProcessedDiff:
            if diff.modifier == "+" and not os.path.exists(diff.file_path):
                raise ValueError(f"File {diff.file_path} does not exist.")

            mime_type = self.__get_mime_type(diff)
            width, height = self.__get_width_height(diff, mime_type)

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
                date_taken=DEFAULT_DATE_TIME,  # Placeholder; will be updated later
                mime_type=mime_type,
                captions=EMPTY_CAPTIONS,
                embedding=EMPTY_EMBEDDING,
            )

        processed_diffs: list[Optional[ProcessedDiff]] = [None] * len(diffs)
        with tqdm(
            total=len(processed_diffs), desc="Fetching simple image metadata"
        ) as pbar:
            with ThreadPoolExecutor() as executor:
                future_to_idx = {
                    executor.submit(process_diff, diff): i
                    for i, diff in enumerate(diffs)
                }
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    processed_diffs[idx] = future.result()
                    pbar.update(1)

        return cast(list[ProcessedDiff], processed_diffs)

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
            if x != '.' and x != os.sep:
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

    def __get_width_height(self, diff: Diff, mime_type: str) -> tuple[int, int]:
        if diff.modifier == '-':
            return 0, 0

        if diff.width is not None and diff.height is not None:
            return diff.width, diff.height

        if is_image(mime_type):
            return get_width_height_of_image(diff.file_path)
        else:
            return get_width_height_of_video(diff.file_path)

    def __get_mime_type(self, diff: Diff) -> str:
        if diff.modifier == '-':
            return 'none'

        if diff.mime_type:
            return diff.mime_type

        try:
            mime_type = magic.from_file(diff.file_path, mime=True)
            return mime_type or "application/octet-stream"
        except Exception as e:
            logger.error(f"Error reading file type: {e}")
            return "application/octet-stream"

    def __populate_processed_diffs_with_exif_metadata(
        self, diffs: list[Diff], processed_diffs: list[ProcessedDiff]
    ) -> list[ProcessedDiff]:
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
        metadatas = [ExtractedExifMetadata(None, DEFAULT_DATE_TIME)] * len(diffs)

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
                        try:
                            date_taken = datetime.strptime(
                                date_str, '%Y:%m:%d %H:%M:%S'
                            )
                        except Exception as e:
                            raise ValueError(
                                f"Invalid date {date_str} at {diffs[i].file_path}"
                            ) from e
                    else:
                        date_taken = datetime(1970, 1, 1)

                metadatas[missing_metadata_and_idx[i][1]] = ExtractedExifMetadata(
                    location, date_taken
                )

        return metadatas

    def __populate_processed_diffs_with_captions(
        self, diffs: list[Diff], processed_diffs: list[ProcessedDiff]
    ) -> list[ProcessedDiff]:
        diffs_to_process: list[Tuple[int, ProcessedDiff]] = [
            (i, processed_diff)
            for i, processed_diff in enumerate(processed_diffs)
            if processed_diff.modifier == "+"
            and processed_diff.mime_type
            and is_image(processed_diff.mime_type)
        ]

        updated_processed_diffs = processed_diffs.copy()

        def load_images(diff_batch):
            images = []
            for _, diff in diff_batch:
                with Image.open(diff.file_path) as img:
                    images.append(img.convert("RGB").copy())
            return images

        with tqdm(
            total=len(diffs_to_process), desc="Generating image captions"
        ) as pbar:
            for start in range(0, len(diffs_to_process), self.captions_batch_size):
                batch = diffs_to_process[start : start + self.captions_batch_size]
                images = load_images(batch)

                captions = self.image_captions.generate_caption(images)
                for idx_in_batch, (proc_idx, _) in enumerate(batch):
                    updated_processed_diffs[proc_idx] = replace(
                        updated_processed_diffs[proc_idx],
                        captions=captions[idx_in_batch],
                    )
                    pbar.update(1)

        return updated_processed_diffs

    def __populate_processed_diffs_with_embeddings(
        self, diffs: list[Diff], processed_diffs: list[ProcessedDiff]
    ) -> list[ProcessedDiff]:
        diffs_to_process: list[Tuple[int, ProcessedDiff]] = [
            (i, processed_diff)
            for i, processed_diff in enumerate(processed_diffs)
            if processed_diff.modifier == "+"
            and processed_diff.mime_type
            and is_image(processed_diff.mime_type)
        ]

        updated_processed_diffs = processed_diffs.copy()

        def load_images(diff_batch):
            images = []
            for _, diff in diff_batch:
                with Image.open(diff.file_path) as img:
                    images.append(img.convert("RGB").copy())
            return images

        with tqdm(
            total=len(diffs_to_process), desc="Generating image embeddings"
        ) as pbar:
            for start in range(0, len(diffs_to_process), self.embedder_batch_size):
                batch = diffs_to_process[start : start + self.embedder_batch_size]
                images = load_images(batch)

                embeddings = self.image_embedder.embed_images(images)
                for idx_in_batch, (proc_idx, _) in enumerate(batch):
                    updated_processed_diffs[proc_idx] = replace(
                        updated_processed_diffs[proc_idx],
                        embedding=embeddings[idx_in_batch],
                    )
                    pbar.update(1)

        return updated_processed_diffs
