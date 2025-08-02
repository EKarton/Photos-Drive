import os
import unittest
import numpy as np
from PIL import Image

from photos_drive.shared.llm.models.open_clip_image_embeddings import (
    OpenCLIPImageEmbeddings,
)


class TestOpenCLIPEmbeddings(unittest.TestCase):
    embedding_model: OpenCLIPImageEmbeddings
    images: list[Image.Image]

    @classmethod
    def setUpClass(cls):
        cls.embedding_model = OpenCLIPImageEmbeddings()

        folder = 'tests/shared/llm/models/test_files'
        image_filenames = ["test_image_1.png", "test_image_2.png"]
        cls.images = []
        for fname in image_filenames:
            path = os.path.join(folder, fname)
            img = Image.open(path).convert("RGB")
            cls.images.append(img)

    def test_embed_texts(self):
        texts = ["hello world", "test embedding"]
        embeddings = self.embedding_model.embed_texts(texts)

        self.assertEqual(embeddings.shape[0], len(texts))
        self.assertGreater(embeddings.shape[1], 0)

        # Check embeddings are normalized (L2 norm ~ 1)
        norms = np.linalg.norm(embeddings, axis=1)
        np.testing.assert_allclose(norms, 1.0, rtol=1e-3)

    def test_embed_images(self):
        embeddings = self.embedding_model.embed_images(self.images)

        self.assertEqual(embeddings.shape[0], len(self.images))
        self.assertGreater(embeddings.shape[1], 758)
        self.assertEqual(embeddings.dtype, np.float32)

        # Check embeddings are normalized
        norms = np.linalg.norm(embeddings, axis=1)
        np.testing.assert_allclose(norms, 1.0, rtol=1e-3)
