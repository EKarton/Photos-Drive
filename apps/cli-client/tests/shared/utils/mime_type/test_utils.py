import unittest

from photos_drive.shared.utils.mime_type.utils import is_image


class TestIsImage(unittest.TestCase):
    def test_common_image_types(self):
        self.assertTrue(is_image("image/jpeg"))
        self.assertTrue(is_image("image/png"))
        self.assertTrue(is_image("image/gif"))
        self.assertTrue(is_image("image/webp"))
        self.assertTrue(is_image("image/svg+xml"))

    def test_non_image_types(self):
        self.assertFalse(is_image("application/pdf"))
        self.assertFalse(is_image("text/plain"))
        self.assertFalse(is_image("video/mp4"))
        self.assertFalse(is_image("audio/mpeg"))

    def test_empty_string(self):
        self.assertFalse(is_image(""))

    def test_invalid_strings(self):
        self.assertFalse(is_image("image"))
        self.assertFalse(is_image("img/jpeg"))
