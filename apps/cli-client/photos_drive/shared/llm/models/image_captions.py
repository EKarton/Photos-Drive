from abc import ABC, abstractmethod

from PIL import Image


class ImageCaptions(ABC):
    '''
    A base class for generating any type of image captions
    '''

    @abstractmethod
    def generate_caption(self, images: list[Image.Image]) -> list[str]:
        '''
        Generates captions from a list of images

        Args:
            - images (list[Image.Image]): A list of images
        Returns:
            list[str]: A list of captions, where captions[i] is
                the caption for images[i]
        '''
