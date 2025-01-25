import unittest
from unittest.mock import MagicMock
from bson import ObjectId

from sharded_photos_drive_cli_client.backup.diffs_assignments import DiffsAssigner
from sharded_photos_drive_cli_client.backup.processed_diffs import ProcessedDiff
from sharded_photos_drive_cli_client.shared.config.config import Config

MOCK_FILE_HASH = b'\x8a\x19\xdd\xdeg\xdd\x96\xf2'


class TestDiffsAssigner(unittest.TestCase):
    def setUp(self):
        """Set up a new DiffsAssigner instance for each test."""
        self.config = MagicMock(spec=Config)
        self.diffs_assigner = DiffsAssigner(self.config)

    def test_get_diffs_assignments__spreads_diffs_across_clients(self):
        client1 = MagicMock()
        client1.get_storage_quota.return_value.limit = 1000
        client1.get_storage_quota.return_value.usage = 500
        client2 = MagicMock()
        client2.get_storage_quota.return_value.limit = 2000
        client2.get_storage_quota.return_value.usage = 1000
        self.config.get_gphotos_clients.return_value = [
            (ObjectId(), client1),
            (ObjectId(), client2),
        ]

        # Create processed diffs with "+" modifier
        diff1 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo1.jpg",
            file_size=300,
            album_name='Archives',
            file_name='photo1.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
        )
        diff2 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo2.jpg",
            file_size=600,
            album_name='Archives',
            file_name='photo2.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
        )
        assignments = self.diffs_assigner.get_diffs_assignments([diff1, diff2])

        self.assertEqual(len(assignments), 2)
        self.assertIn(diff1, assignments)
        self.assertIn(diff2, assignments)

    def test_get_diffs_assignments__no_available_space__throws_error(self):
        client1 = MagicMock()
        client1.get_storage_quota.return_value.limit = 1000
        client1.get_storage_quota.return_value.usage = 1000  # No space left
        self.config.get_gphotos_clients.return_value = [
            (ObjectId(), client1),
        ]

        diff1 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo1.jpg",
            file_size=300,
            album_name='Archives',
            file_name='photo1.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
        )
        with self.assertRaisesRegex(
            ValueError, "Cannot allocate .* to any GPhotos client"
        ):
            self.diffs_assigner.get_diffs_assignments([diff1])

    def test_get_diffs_assignments__no_assignment_possible__throws_error(self):
        # Mocking Google Photos clients with limited space
        client1 = MagicMock()
        client1.get_storage_quota.return_value.limit = 1000
        client1.get_storage_quota.return_value.usage = 400
        client2 = MagicMock()
        client2.get_storage_quota.return_value.limit = 500
        client2.get_storage_quota.return_value.usage = 200
        self.config.get_gphotos_clients.return_value = [
            (ObjectId(), client1),
            (ObjectId(), client2),
        ]

        diff1 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo1.jpg",
            file_size=300,
            album_name='Archives',
            file_name='photo1.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
        )
        diff2 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo2.jpg",
            file_size=400,
            album_name='Archives',
            file_name='photo2.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
        )
        diff3 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo3.jpg",
            file_size=500,
            album_name='Archives',
            file_name='photo3.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
        )

        with self.assertRaisesRegex(
            ValueError, "Cannot allocate .* to any GPhotos client"
        ):
            self.diffs_assigner.get_diffs_assignments([diff1, diff2, diff3])
