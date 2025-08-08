from datetime import datetime, timezone
import unittest

from photos_drive.backup.diffs import Diff
from photos_drive.backup.processed_diffs import (
    EMPTY_EMBEDDING,
    DiffsProcessor,
    ProcessedDiff,
)
from photos_drive.shared.llm.models.testing.fake_image_embedder import (
    FAKE_EMBEDDING,
    FakeImageEmbedder,
)
from photos_drive.shared.metadata.gps_location import GpsLocation
from photos_drive.shared.utils.hashes.xxhash import compute_file_hash

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
            "large_image.jpg",
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

        processor = DiffsProcessor(FakeImageEmbedder())
        processed_diffs = processor.process_raw_diffs(diffs)
        self.assertEqual(len(processed_diffs), 7)
        self.assertEqual(
            processed_diffs[0],
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
                mime_type='image/heic',
                embedding=FAKE_EMBEDDING,
            ),
        )
        self.assertEqual(
            processed_diffs[1],
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
                mime_type='image/jpeg',
                embedding=FAKE_EMBEDDING,
            ),
        )
        self.assertEqual(
            processed_diffs[2],
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
                mime_type='image/jpeg',
                embedding=FAKE_EMBEDDING,
            ),
        )
        self.assertEqual(
            processed_diffs[3],
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
                mime_type='image/jpeg',
                embedding=FAKE_EMBEDDING,
            ),
        )
        self.assertEqual(
            processed_diffs[4],
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
                mime_type='image/heic',
                embedding=FAKE_EMBEDDING,
            ),
        )
        self.assertEqual(
            processed_diffs[5],
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
                mime_type='video/quicktime',
                embedding=EMPTY_EMBEDDING,
            ),
        )
        # self.assertIsNone(processed_diffs[6])
        self.assertEqual(
            processed_diffs[6],
            ProcessedDiff(
                modifier='+',
                file_path=diffs[6].file_path,
                album_name='tests/backup/resources/test_processed_diffs_files',
                file_name='large_image.jpg',
                file_size=53020032,
                file_hash=b'\xd8\xc5\xc2\xfa\xcf\xe8\xce?',
                location=GpsLocation(
                    latitude=46.8118727000028, longitude=-71.2053023999556
                ),
                width=10016,
                height=3872,
                date_taken=datetime(2018, 12, 25, 13, 15, 27),
                mime_type='image/jpeg',
                embedding=EMPTY_EMBEDDING,
            ),
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
            date_taken=datetime(2010, 2, 2),
            mime_type="image/png",
        )

        processor = DiffsProcessor(FakeImageEmbedder())
        processed_diffs = processor.process_raw_diffs([diff])

        self.assertEqual(len(processed_diffs), 1)
        self.assertEqual(processed_diffs[0].album_name, 'Photos/2010')
        self.assertEqual(processed_diffs[0].file_name, 'dog.png')
        self.assertEqual(processed_diffs[0].file_size, 1000)
        self.assertEqual(processed_diffs[0].location, GpsLocation(100, 200))
        self.assertEqual(
            processed_diffs[0].file_hash, compute_file_hash(test_file_path)
        )
        self.assertEqual(processed_diffs[0].date_taken, datetime(2010, 2, 2))
        self.assertEqual(processed_diffs[0].mime_type, 'image/png')

    def test_process_raw_diffs_with_no_date_taken(self):
        test_file_path = self.__get_file_path("image-without-dates.jpg")
        diff = Diff(
            modifier="+",
            file_path=test_file_path,
        )

        processor = DiffsProcessor(FakeImageEmbedder())
        processed_diffs = processor.process_raw_diffs([diff])

        self.assertEqual(len(processed_diffs), 1)
        self.assertEqual(
            processed_diffs[0].album_name,
            'tests/backup/resources/test_processed_diffs_files',
        )
        self.assertEqual(processed_diffs[0].file_name, 'image-without-dates.jpg')
        self.assertEqual(processed_diffs[0].file_size, 2620046)
        self.assertEqual(processed_diffs[0].location, None)
        self.assertEqual(
            processed_diffs[0].file_hash, compute_file_hash(test_file_path)
        )
        self.assertEqual(processed_diffs[0].date_taken, datetime(1970, 1, 1))
        self.assertEqual(processed_diffs[0].mime_type, 'image/jpeg')

    def test_process_raw_diffs_with_deletion_diff(self):
        test_file_path = self.__get_file_path('image-with-location.jpg')
        diff = Diff(
            modifier="-",
            file_path=test_file_path,
            album_name=None,
            file_name=None,
        )

        processor = DiffsProcessor(FakeImageEmbedder())
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
        self.assertEqual(processed_diffs[0].width, 0)
        self.assertEqual(processed_diffs[0].height, 0)
        self.assertEqual(processed_diffs[0].date_taken, datetime(1970, 1, 1))
        self.assertEqual(processed_diffs[0].mime_type, 'none')
        self.assertEqual(processed_diffs[0].embedding, EMPTY_EMBEDDING)

    def test_process_raw_diffs_file_not_exist(self):
        diff = Diff(
            modifier="+", file_path="path/to/nonexistent_photo.jpg", album_name=None
        )

        with self.assertRaisesRegex(ValueError, "File .* does not exist."):
            processor = DiffsProcessor(FakeImageEmbedder())
            processor.process_raw_diffs([diff])

    def __get_file_path(self, file_name: str) -> str:
        return f"./tests/backup/resources/test_processed_diffs_files/{file_name}"
