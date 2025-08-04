from datetime import datetime, timezone
import unittest
from io import StringIO
from unittest.mock import patch

from photos_drive.backup.diffs import Diff
from photos_drive.backup.processed_diffs import ProcessedDiff
from photos_drive.cli.shared.printer import (
    pretty_print_diffs,
    pretty_print_processed_diffs,
)
from photos_drive.shared.llm.models.testing.fake_image_embedder import FAKE_EMBEDDING
from photos_drive.shared.metadata.media_items import GpsLocation

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0, tzinfo=timezone.utc)


class TestPrettyPrintProcessedDiffs(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def test_pretty_print_processed_diffs(self, mock_stdout):
        processed_diffs = [
            ProcessedDiff(
                modifier='+',
                file_path='Test/file1.jpg',
                album_name='Test',
                file_name="file1.png",
                file_hash=b'hash1',
                location=None,
                file_size=1000,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/jpeg',
                embedding=FAKE_EMBEDDING,
            ),
            ProcessedDiff(
                modifier='-',
                file_path='Test/file2.png',
                album_name='Test',
                file_name="file2.png",
                file_hash=b'hash2',
                location=GpsLocation(latitude=40, longitude=100),
                file_size=2000,
                width=100,
                height=200,
                date_taken=MOCK_DATE_TAKEN,
                mime_type='image/png',
                embedding=FAKE_EMBEDDING,
            ),
        ]

        pretty_print_processed_diffs(processed_diffs)

        output = mock_stdout.getvalue()
        self.assertIn('file1.jpg', output)
        self.assertIn('file2.png', output)
        self.assertIn('40, 100', output)
        self.assertIn('Number of media items to add: 1', output)
        self.assertIn('Number of media items to delete: 1', output)


class TestPrettyPrintDiffs(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def test_pretty_print_diffs(self, mock_stdout):
        diffs = [Diff('+', 'file1.jpg'), Diff('-', 'file2.png')]

        pretty_print_diffs(diffs)

        output = mock_stdout.getvalue()
        self.assertIn('file1.jpg', output)
        self.assertIn('file2.png', output)
        self.assertIn('Number of media items to add: 1', output)
        self.assertIn('Number of media items to delete: 1', output)
