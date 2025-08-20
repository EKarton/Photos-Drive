import logging

from PIL import Image
import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor
from typing_extensions import override

from photos_drive.shared.llm.models.image_embeddings import ImageEmbeddings

logger = logging.getLogger(__name__)


class OpenCLIPImageEmbeddings(ImageEmbeddings):
    def __init__(self, model_name="openai/clip-vit-large-patch14", device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32

        self.model = CLIPModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            use_safetensors=True,
            torch_dtype=self.dtype,
        ).to(self.device)

        self.processor = CLIPProcessor.from_pretrained(model_name)

    @override
    def get_embedding_dimension(self) -> int:
        return self.model.config.projection_dim

    @override
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        inputs = self.processor(text=texts, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            embeddings = self.model.get_text_features(**inputs)
        embeddings = embeddings / embeddings.norm(p=2, dim=-1, keepdim=True)
        return embeddings.cpu().numpy()

    @override
    def embed_images(self, images: list[Image.Image]) -> np.ndarray:
        inputs = self.processor(images=images, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            embeddings = self.model.get_image_features(**inputs)
        embeddings = embeddings / embeddings.norm(p=2, dim=-1, keepdim=True)
        return embeddings.cpu().numpy()
