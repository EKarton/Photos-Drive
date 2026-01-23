from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock

from bson import ObjectId
import numpy as np

from photos_drive.backup.diffs_assignments import DiffsAssigner
from photos_drive.backup.processed_diffs import ProcessedDiff
from photos_drive.shared.features.llm.models.testing.fake_image_captions import FAKE_CAPTIONS
from photos_drive.shared.core.storage.gphotos.clients_repository import (
    GPhotosClientsRepository,
)

MOCK_FILE_HASH = b'\x8a\x19\xdd\xdeg\xdd\x96\xf2'

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0, tzinfo=timezone.utc)

MOCK_EMBEDDING = np.array([0.1, 0.5, -0.3])


class TestDiffsAssigner(unittest.TestCase):
    def test_get_diffs_assignments__spreads_diffs_across_clients(self):
        client1 = MagicMock()
        client1.get_storage_quota.return_value.limit = 1000
        client1.get_storage_quota.return_value.usage = 500
        client2 = MagicMock()
        client2.get_storage_quota.return_value.limit = 2000
        client2.get_storage_quota.return_value.usage = 1000
        repo = GPhotosClientsRepository()
        repo.add_gphotos_client(ObjectId(), client1)
        repo.add_gphotos_client(ObjectId(), client2)

        # Create processed diffs with "+" modifier
        diffs_assigner = DiffsAssigner(repo)
        diff1 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo1.jpg",
            file_size=300,
            album_name='Archives',
            file_name='photo1.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
            width=100,
            height=200,
            date_taken=MOCK_DATE_TAKEN,
            mime_type='image/jpeg',
            captions=FAKE_CAPTIONS,
            embedding=MOCK_EMBEDDING,
        )
        diff2 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo2.jpg",
            file_size=600,
            album_name='Archives',
            file_name='photo2.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
            width=100,
            height=200,
            date_taken=MOCK_DATE_TAKEN,
            mime_type='image/jpeg',
            captions=FAKE_CAPTIONS,
            embedding=MOCK_EMBEDDING,
        )
        assignments = diffs_assigner.get_diffs_assignments([diff1, diff2])

        self.assertEqual(len(assignments), 2)
        self.assertIn(diff1, assignments)
        self.assertIn(diff2, assignments)

    def test_get_diffs_assignments__no_available_space__throws_error(self):
        client1 = MagicMock()
        client1.get_storage_quota.return_value.limit = 1000
        client1.get_storage_quota.return_value.usage = 1000  # No space left
        repo = GPhotosClientsRepository()
        repo.add_gphotos_client(ObjectId(), client1)

        diffs_assigner = DiffsAssigner(repo)
        diff1 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo1.jpg",
            file_size=300,
            album_name='Archives',
            file_name='photo1.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
            width=100,
            height=200,
            date_taken=MOCK_DATE_TAKEN,
            mime_type='image/jpeg',
            captions=FAKE_CAPTIONS,
            embedding=MOCK_EMBEDDING,
        )
        with self.assertRaisesRegex(
            ValueError, "Cannot allocate .* to any GPhotos client"
        ):
            diffs_assigner.get_diffs_assignments([diff1])

    def test_get_diffs_assignments__no_assignment_possible__throws_error(self):
        # Mocking Google Photos clients with limited space
        client1 = MagicMock()
        client1.get_storage_quota.return_value.limit = 1000
        client1.get_storage_quota.return_value.usage = 400
        client2 = MagicMock()
        client2.get_storage_quota.return_value.limit = 500
        client2.get_storage_quota.return_value.usage = 200
        repo = GPhotosClientsRepository()
        repo.add_gphotos_client(ObjectId(), client1)
        repo.add_gphotos_client(ObjectId(), client2)

        diffs_assigner = DiffsAssigner(repo)
        diff1 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo1.jpg",
            file_size=300,
            album_name='Archives',
            file_name='photo1.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
            width=100,
            height=200,
            date_taken=MOCK_DATE_TAKEN,
            mime_type='image/jpeg',
            captions=FAKE_CAPTIONS,
            embedding=MOCK_EMBEDDING,
        )
        diff2 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo2.jpg",
            file_size=400,
            album_name='Archives',
            file_name='photo2.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
            width=100,
            height=200,
            date_taken=MOCK_DATE_TAKEN,
            mime_type='image/jpeg',
            captions=FAKE_CAPTIONS,
            embedding=MOCK_EMBEDDING,
        )
        diff3 = ProcessedDiff(
            modifier="+",
            file_path="Archives/photo3.jpg",
            file_size=500,
            album_name='Archives',
            file_name='photo3.jpg',
            location=None,
            file_hash=MOCK_FILE_HASH,
            width=100,
            height=200,
            date_taken=MOCK_DATE_TAKEN,
            mime_type='image/jpeg',
            captions=FAKE_CAPTIONS,
            embedding=MOCK_EMBEDDING,
        )

        with self.assertRaisesRegex(
            ValueError, "Cannot allocate .* to any GPhotos client"
        ):
            diffs_assigner.get_diffs_assignments([diff1, diff2, diff3])
