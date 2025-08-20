from PIL import Image
from typing_extensions import override

from photos_drive.shared.llm.models.image_captions import ImageCaptions

FAKE_CAPTIONS = 'Sample captions'


class FakeImageCaptions(ImageCaptions):
    '''
    Generates fake captions for any image
    '''

    @override
    def generate_caption(self, images: list[Image.Image]) -> list[str]:
        return [FAKE_CAPTIONS for _ in images]
