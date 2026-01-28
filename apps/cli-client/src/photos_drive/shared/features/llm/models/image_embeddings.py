from abc import ABC, abstractmethod

from PIL import Image
import numpy as np


class ImageEmbeddings(ABC):
    '''
    This is the base class to get the embeddings of an image and text
    in the same vector space.
    '''

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        '''
        Returns the embedding dimension size D of the model (ex: 768)
        '''

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        '''
        Returns the embeddings of a list of text

        Args:
            - texts (list[str]): A list of strings.

        Returns:
            np.ndarray: A list of N x D embeddings, where N = number of strings
                and D = embedding dimension size
        '''

    @abstractmethod
    def embed_images(self, images: list[Image.Image]) -> np.ndarray:
        '''
        Returns the embeddings of a list of images
        It generates embeddings in parallel in {@code batch_size} images.

        Args:
            - images (list[Image.Image]): A list of images.

        Returns:
            np.ndarray: A list of N x D embeddings, where N = number of images
                and D = embedding dimension size
        '''
