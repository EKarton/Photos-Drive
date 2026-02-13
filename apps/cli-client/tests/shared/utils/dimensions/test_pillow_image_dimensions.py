import os
import unittest

from photos_drive.shared.utils.dimensions.pillow_image_dimensions import (
    get_width_height_of_image,
)

PHOTOS_DIRECTORY = "./tests/shared/utils/dimensions/test_files"


class PillowImageDimensionsTests(unittest.TestCase):
    def test_get_width_height_of_image(self):
        file_path = os.path.join(PHOTOS_DIRECTORY, "image.jpg")
        width, height = get_width_height_of_image(file_path)

        self.assertEqual(width, 3264)
        self.assertEqual(height, 2448)

    def test_get_width_height_of_image_of_rotated_image(self):
        file_path = os.path.join(PHOTOS_DIRECTORY, "rotated-image.jpg")
        width, height = get_width_height_of_image(file_path)

        self.assertEqual(width, 2448)
        self.assertEqual(height, 3264)
