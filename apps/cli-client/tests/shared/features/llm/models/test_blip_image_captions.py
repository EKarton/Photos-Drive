import os
import unittest

from PIL import Image

from photos_drive.shared.features.llm.models.blip_image_captions import (
    BlipImageCaptions,
)


class TestBlipImageCaptions(unittest.TestCase):
    caption_model: BlipImageCaptions
    images: list[Image.Image]

    @classmethod
    def setUpClass(cls):
        cls.caption_model = BlipImageCaptions()

        folder = 'tests/shared/features/llm/models/test_files'
        image_filenames = ["test_image_1.png", "test_image_2.png"]
        cls.images = []
        for fname in image_filenames:
            path = os.path.join(folder, fname)
            img = Image.open(path).convert("RGB")
            cls.images.append(img)

    def test_generate_caption_on_sample_images(self):
        captions = self.caption_model.generate_caption(self.images)

        self.assertEqual(
            captions,
            [
                'a globe with a grid of lines on it',
                'a map with different apps on it',
            ],
        )
