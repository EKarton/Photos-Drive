import unittest
from unittest.mock import patch

from sharded_photos_drive_cli_client.backup.diffs import Diff
from sharded_photos_drive_cli_client.backup.processed_diffs import DiffsProcessor
from sharded_photos_drive_cli_client.shared.mongodb.media_items import GpsLocation


class TestDiffsProcessor(unittest.TestCase):
    def test_process_raw_diffs__image_with_location__returns_processed_diffs_correctly(
        self,
    ):
        test_file_path = "./tests/backup/resources/test_processed_diffs_files/image-with-location.jpg"
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
        self.assertEqual(processed_diffs[0].location.latitude, 43.12446492202323)
        self.assertEqual(processed_diffs[0].location.longitude, -79.06879274830213)

    def test_process_raw_diffs__image_with_inversed_location__returns_processed_diffs_correctly(
        self,
    ):
        test_file_path = "./tests/backup/resources/test_processed_diffs_files/image-with-location-2.jpg"
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
        self.assertEqual(processed_diffs[0].location.latitude, -40.7128)
        self.assertEqual(processed_diffs[0].location.longitude, -74.006)

    def test_process_raw_diffs__image_with_no_location__returns_processed_diffs_correctly(
        self,
    ):
        test_file_path = "./tests/backup/resources/test_processed_diffs_files/image-without-location.jpg"
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

    @patch('exifread.process_file')
    def test_process_raw_diffs__exifread_throws_error__returns_processed_diffs_correctly(
        self, mock_process_file
    ):
        mock_process_file.side_effect = Exception("Error reading EXIF data")
        test_file_path = "./tests/backup/resources/test_processed_diffs_files/image-with-location.jpg"
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
        self.assertIsNone(processed_diffs[0].location)

    def test_process_raw_diffs__with_fields_set__returns_processed_diffs_with_fields_set(
        self,
    ):
        test_file_path = "./tests/backup/resources/test_processed_diffs_files/image-with-location.jpg"
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
        self.assertEqual(processed_diffs[0].location.latitude, 100)
        self.assertEqual(processed_diffs[0].location.longitude, 200)

    def test_process_raw_diffs__with_deletion_diff__returns_processed_diffs_correctly(
        self,
    ):
        test_file_path = "./tests/backup/resources/test_processed_diffs_files/image-with-location.jpg"
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
