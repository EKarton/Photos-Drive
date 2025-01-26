from typing import cast
import unittest

from sharded_photos_drive_cli_client.backup.diffs import Diff
from sharded_photos_drive_cli_client.backup.processed_diffs import DiffsProcessor
from sharded_photos_drive_cli_client.shared.hashes.xxhash import compute_file_hash
from sharded_photos_drive_cli_client.shared.mongodb.media_items import GpsLocation


class TestDiffsProcessor(unittest.TestCase):
    def test_process_raw_diffs_image_with_location(self):
        test_file_path = (
            "./tests/backup/resources/test_processed_diffs_files"
            + "/image-with-location.jpg"
        )
        diff = Diff(
            modifier="+",
            file_path=test_file_path,
            album_name=None,
            file_name=None,
        )

        processor = DiffsProcessor()
        processed_diffs = processor.process_raw_diffs([diff])

        self.assertEqual(len(processed_diffs), 1)
        self.assertEqual(processed_diffs[0].modifier, '+')
        self.assertEqual(processed_diffs[0].file_path, test_file_path)
        self.assertEqual(
            processed_diffs[0].album_name,
            'tests/backup/resources/test_processed_diffs_files',
        )
        self.assertEqual(processed_diffs[0].file_name, "image-with-location.jpg")
        self.assertEqual(processed_diffs[0].file_size, 2622777)
        self.assertEqual(
            cast(GpsLocation, processed_diffs[0].location).latitude, 43.1244649220222
        )
        self.assertEqual(
            cast(GpsLocation, processed_diffs[0].location).longitude, -79.0687927483022
        )
        self.assertEqual(
            processed_diffs[0].file_hash, compute_file_hash(test_file_path)
        )

    def test_process_raw_diffs_heif_image_location(self):
        test_file_path = (
            "./tests/backup/resources/test_processed_diffs_files/heic-image.heic"
        )
        diff = Diff(
            modifier="+",
            file_path=test_file_path,
            album_name=None,
            file_name=None,
        )

        processor = DiffsProcessor()
        processed_diffs = processor.process_raw_diffs([diff])

        self.assertEqual(len(processed_diffs), 1)
        self.assertEqual(processed_diffs[0].modifier, '+')
        self.assertEqual(processed_diffs[0].file_path, test_file_path)
        self.assertEqual(
            processed_diffs[0].album_name,
            'tests/backup/resources/test_processed_diffs_files',
        )
        self.assertEqual(processed_diffs[0].file_name, "heic-image.heic")
        self.assertEqual(processed_diffs[0].file_size, 3271280)
        self.assertEqual(
            cast(GpsLocation, processed_diffs[0].location).latitude, 40.7425527777778
        )
        self.assertEqual(
            cast(GpsLocation, processed_diffs[0].location).longitude, -74.0101694444444
        )
        self.assertEqual(
            processed_diffs[0].file_hash, compute_file_hash(test_file_path)
        )

    def test_process_raw_diffs_image_with_inversed_location(self):
        test_file_path = (
            "./tests/backup/resources/test_processed_diffs_files"
            + "/image-with-location-2.jpg"
        )
        diff = Diff(
            modifier="+",
            file_path=test_file_path,
            album_name=None,
            file_name=None,
        )

        processor = DiffsProcessor()
        processed_diffs = processor.process_raw_diffs([diff])

        self.assertEqual(len(processed_diffs), 1)
        self.assertEqual(processed_diffs[0].modifier, '+')
        self.assertEqual(processed_diffs[0].file_path, test_file_path)
        self.assertEqual(
            processed_diffs[0].album_name,
            'tests/backup/resources/test_processed_diffs_files',
        )
        self.assertEqual(processed_diffs[0].file_name, "image-with-location-2.jpg")
        self.assertEqual(processed_diffs[0].file_size, 2622777)
        self.assertEqual(processed_diffs[0].location, GpsLocation(-40.7128, -74.006))
        self.assertEqual(
            processed_diffs[0].file_hash, compute_file_hash(test_file_path)
        )

    def test_process_raw_diffs_image_with_no_location(self):
        test_file_path = (
            "./tests/backup/resources/test_processed_diffs_files"
            + "/image-without-location.jpg"
        )
        diff = Diff(
            modifier="+",
            file_path=test_file_path,
            album_name=None,
            file_name=None,
        )

        processor = DiffsProcessor()
        processed_diffs = processor.process_raw_diffs([diff])

        self.assertEqual(len(processed_diffs), 1)
        self.assertEqual(processed_diffs[0].modifier, '+')
        self.assertEqual(processed_diffs[0].file_path, test_file_path)
        self.assertEqual(
            processed_diffs[0].album_name,
            'tests/backup/resources/test_processed_diffs_files',
        )
        self.assertEqual(processed_diffs[0].file_name, "image-without-location.jpg")
        self.assertEqual(processed_diffs[0].file_size, 2622651)
        self.assertIsNone(processed_diffs[0].location)
        self.assertEqual(
            processed_diffs[0].file_hash, compute_file_hash(test_file_path)
        )

    def test_process_raw_diffs_with_fields_set(self):
        test_file_path = (
            "./tests/backup/resources/test_processed_diffs_files"
            + "/image-with-location.jpg"
        )
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
        test_file_path = (
            "./tests/backup/resources/test_processed_diffs_files"
            + "/image-with-location.jpg"
        )
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
        self.assertEqual(
            processed_diffs[0].file_hash, compute_file_hash(test_file_path)
        )

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
