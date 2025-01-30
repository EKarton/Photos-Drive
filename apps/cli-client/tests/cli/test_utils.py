import unittest
from pyfakefs.fake_filesystem_unittest import TestCase
from unittest.mock import patch
from io import StringIO

from sharded_photos_drive_cli_client.backup.diffs import Diff
from sharded_photos_drive_cli_client.backup.processed_diffs import ProcessedDiff
from sharded_photos_drive_cli_client.cli.utils import (
    get_diffs_from_path,
    pretty_print_diffs,
    pretty_print_processed_diffs,
)


class TestGetDiffsFromPath(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_get_diffs_from_path_file(self):
        self.fs.create_file('/test/image.jpg')

        result = get_diffs_from_path('/test/image.jpg')

        self.assertEqual(result, ['/test/image.jpg'])

    def test_get_diffs_from_path_invalid_file(self):
        self.fs.create_file('/test/document.txt')

        with self.assertRaises(ValueError):
            get_diffs_from_path('/test/document.txt')

    def test_get_diffs_from_path_nonexistent(self):
        with self.assertRaises(ValueError):
            get_diffs_from_path('/test/nonexistent.jpg')

    def test_get_diffs_from_dir_path(self):
        self.fs.create_file('/test/image1.jpg')
        self.fs.create_file('/test/image2.png')
        self.fs.create_file('/test/subdir/image3.gif')
        self.fs.create_file('/test/document.txt')

        result = get_diffs_from_path('/test')

        expected = [
            './test/image1.jpg',
            './test/image2.png',
            './test/subdir/image3.gif',
        ]
        self.assertEqual(sorted(result), sorted(expected))


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
