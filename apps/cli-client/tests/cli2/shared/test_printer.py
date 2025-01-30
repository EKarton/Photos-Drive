import unittest
from io import StringIO
from unittest.mock import patch

from sharded_photos_drive_cli_client.backup.diffs import Diff
from sharded_photos_drive_cli_client.backup.processed_diffs import ProcessedDiff
from sharded_photos_drive_cli_client.cli2.shared.printer import (
    pretty_print_diffs,
    pretty_print_processed_diffs,
)


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
            ),
            ProcessedDiff(
                modifier='-',
                file_path='Test/file2.png',
                album_name='Test',
                file_name="file2.png",
                file_hash=b'hash2',
                location=None,
                file_size=2000,
            ),
        ]

        pretty_print_processed_diffs(processed_diffs)

        output = mock_stdout.getvalue()
        self.assertIn('file1.jpg', output)
        self.assertIn('file2.png', output)
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
