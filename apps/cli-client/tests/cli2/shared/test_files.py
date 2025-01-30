from pyfakefs.fake_filesystem_unittest import TestCase

from sharded_photos_drive_cli_client.cli2.shared.files import (
    get_media_file_paths_from_path,
)


class TestGetDiffsFromPath(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_get_diffs_from_path_file(self):
        self.fs.create_file('/test/image.jpg')

        result = get_media_file_paths_from_path('/test/image.jpg')

        self.assertEqual(result, ['/test/image.jpg'])

    def test_get_diffs_from_path_invalid_file(self):
        self.fs.create_file('/test/document.txt')

        with self.assertRaises(ValueError):
            get_media_file_paths_from_path('/test/document.txt')

    def test_get_diffs_from_path_nonexistent(self):
        with self.assertRaises(ValueError):
            get_media_file_paths_from_path('/test/nonexistent.jpg')

    def test_get_diffs_from_dir_path(self):
        self.fs.create_file('/test/image1.jpg')
        self.fs.create_file('/test/image2.png')
        self.fs.create_file('/test/subdir/image3.gif')
        self.fs.create_file('/test/document.txt')

        result = get_media_file_paths_from_path('/test')

        expected = [
            './test/image1.jpg',
            './test/image2.png',
            './test/subdir/image3.gif',
        ]
        self.assertEqual(sorted(result), sorted(expected))
