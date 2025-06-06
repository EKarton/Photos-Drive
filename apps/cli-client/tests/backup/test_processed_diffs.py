from datetime import datetime, timezone
import unittest

from sharded_photos_drive_cli_client.backup.diffs import Diff
from sharded_photos_drive_cli_client.backup.processed_diffs import (
    DiffsProcessor,
    ProcessedDiff,
)
from sharded_photos_drive_cli_client.shared.hashes.xxhash import compute_file_hash
from sharded_photos_drive_cli_client.shared.mongodb.media_items import GpsLocation

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0, tzinfo=timezone.utc)


class TestDiffsProcessor(unittest.TestCase):
    def test_process_raw_diffs_multiple_images(self):
        self.maxDiff = None
        test_file_names = [
            "heic-image.heic",
            "image-with-location-2.jpg",
            "image-with-location.jpg",
            "image-without-location.jpg",
            "heic-image-2.heic",
            "video.mov",
        ]
        diffs = [
            Diff(
                modifier="+",
                file_path=self.__get_file_path(file_name),
                album_name=None,
                file_name=None,
            )
            for file_name in test_file_names
        ]

        processor = DiffsProcessor()
        processed_diffs = processor.process_raw_diffs(diffs)
        self.assertEqual(
            processed_diffs,
            [
                ProcessedDiff(
                    modifier='+',
                    file_path=diffs[0].file_path,
                    album_name='tests/backup/resources/test_processed_diffs_files',
                    file_name='heic-image.heic',
                    file_size=3271280,
                    file_hash=b'\xe60\xb7\xb6h(Z/',
                    location=GpsLocation(
                        latitude=40.7425527777778, longitude=-74.0101694444444
                    ),
                    width=4032,
                    height=3024,
                    date_taken=datetime(2022, 11, 18, 16, 39, 21),
                ),
                ProcessedDiff(
                    modifier='+',
                    file_path=diffs[1].file_path,
                    album_name='tests/backup/resources/test_processed_diffs_files',
                    file_name='image-with-location-2.jpg',
                    file_size=2622777,
                    file_hash=b'l\x94Y\xa2\xa4W\x06\x1a',
                    location=GpsLocation(latitude=-40.7128, longitude=-74.006),
                    width=3264,
                    height=2448,
                    date_taken=datetime(2013, 5, 30, 10, 30, 39),
                ),
                ProcessedDiff(
                    modifier='+',
                    file_path=diffs[2].file_path,
                    album_name='tests/backup/resources/test_processed_diffs_files',
                    file_name='image-with-location.jpg',
                    file_size=2622777,
                    file_hash=b'dK\xbb\x80\x8d\x88T\xa1',
                    location=GpsLocation(
                        latitude=43.1244649220222, longitude=-79.0687927483022
                    ),
                    width=3264,
                    height=2448,
                    date_taken=datetime(2013, 5, 30, 10, 30, 39),
                ),
                ProcessedDiff(
                    modifier='+',
                    file_path=diffs[3].file_path,
                    album_name='tests/backup/resources/test_processed_diffs_files',
                    file_name='image-without-location.jpg',
                    file_size=2622651,
                    file_hash=b'v\x04\x83s]\xe3tw',
                    location=None,
                    width=3264,
                    height=2448,
                    date_taken=datetime(2013, 5, 30, 10, 30, 39),
                ),
                ProcessedDiff(
                    modifier='+',
                    file_path=diffs[4].file_path,
                    album_name='tests/backup/resources/test_processed_diffs_files',
                    file_name='heic-image-2.heic',
                    file_size=3054916,
                    file_hash=b'\xd0\xf5m\xdc\xfaI\x1dc',
                    location=GpsLocation(
                        latitude=39.1834944444444, longitude=-119.926863888889
                    ),
                    width=4032,
                    height=3024,
                    date_taken=datetime(2022, 6, 20, 15, 15, 53),
                ),
                ProcessedDiff(
                    modifier='+',
                    file_path=diffs[5].file_path,
                    album_name='tests/backup/resources/test_processed_diffs_files',
                    file_name='video.mov',
                    file_size=2571720,
                    file_hash=b'\xc6K\xa09\x17Wq\x9d',
                    location=GpsLocation(latitude=40.1872, longitude=-121.1004),
                    width=1744,
                    height=1308,
                    date_taken=datetime(2022, 5, 29, 11, 19, 1),
                ),
            ],
        )

    def test_process_raw_diffs_with_fields_set(self):
        test_file_path = self.__get_file_path("image-with-location.jpg")
        diff = Diff(
            modifier="+",
            file_path=test_file_path,
            album_name='Photos/2010',
            file_name='dog.png',
            file_size=1000,
            location=GpsLocation(latitude=100, longitude=200),
        )

        processor = DiffsProcessor()
        processed_diffs = processor.process_raw_diffs([diff])

        self.assertEqual(len(processed_diffs), 1)
        self.assertEqual(processed_diffs[0].album_name, 'Photos/2010')
        self.assertEqual(processed_diffs[0].file_name, 'dog.png')
        self.assertEqual(processed_diffs[0].file_size, 1000)
        self.assertEqual(processed_diffs[0].location, GpsLocation(100, 200))
        self.assertEqual(
            processed_diffs[0].file_hash, compute_file_hash(test_file_path)
        )

    def test_process_raw_diffs_with_deletion_diff(self):
        test_file_path = self.__get_file_path('image-with-location.jpg')
        diff = Diff(
            modifier="-",
            file_path=test_file_path,
            album_name=None,
            file_name=None,
        )

        processor = DiffsProcessor()
        processed_diffs = processor.process_raw_diffs([diff])

        self.assertEqual(len(processed_diffs), 1)
        self.assertEqual(processed_diffs[0].modifier, '-')
        self.assertEqual(processed_diffs[0].file_path, test_file_path)
        self.assertEqual(
            processed_diffs[0].album_name,
            'tests/backup/resources/test_processed_diffs_files',
        )
        self.assertEqual(processed_diffs[0].file_name, "image-with-location.jpg")
        self.assertEqual(processed_diffs[0].file_size, 0)
        self.assertIsNone(processed_diffs[0].location)
        self.assertEqual(processed_diffs[0].file_hash, b'0')

    def test_process_raw_diffs_file_not_exist(self):
        diff = Diff(
            modifier="+", file_path="path/to/nonexistent_photo.jpg", album_name=None
        )

        with self.assertRaisesRegex(ValueError, "File .* does not exist."):
            processor = DiffsProcessor()
            processor.process_raw_diffs([diff])

    def test_process_raw_diffs_invalid_modifier(self):
        diff = Diff(modifier="*", file_path="path/to/photo.jpg")

        with self.assertRaisesRegex(ValueError, "Modifier * .*"):
            processor = DiffsProcessor()
            processor.process_raw_diffs([diff])

    def __get_file_path(self, file_name: str) -> str:
        return f"./tests/backup/resources/test_processed_diffs_files/{file_name}"
