import os
import unittest

from photos_drive.shared.utils.dimensions.cv2_video_dimensions import (
    get_width_height_of_video,
)

VIDEOS_DIRECTORY = "./tests/shared/utils/dimensions/test_files"


class CV2VideoDimensionsTests(unittest.TestCase):
    def test_get_width_height_of_video(self):
        file_path = os.path.join(VIDEOS_DIRECTORY, "video.mp4")
        width, height = get_width_height_of_video(file_path)

        self.assertEqual(width, 120)
        self.assertEqual(height, 68)

    def test_get_width_height_of_video_of_rotated_video(self):
        file_path = os.path.join(VIDEOS_DIRECTORY, "rotated-video.mp4")
        width, height = get_width_height_of_video(file_path)

        self.assertEqual(width, 68)
        self.assertEqual(height, 120)
