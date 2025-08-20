import logging

from PIL import Image
import torch
from transformers import BlipForConditionalGeneration, BlipProcessor
from typing_extensions import override

from photos_drive.shared.llm.models.image_captions import ImageCaptions

logger = logging.getLogger(__name__)


class BlipImageCaptions(ImageCaptions):
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32

        self.blip_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base",
            trust_remote_code=True,
            use_safetensors=True,
            torch_dtype=self.dtype,
        ).to(self.device)

        self.blip_processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )

    @override
    def generate_caption(self, images: list[Image.Image]) -> list[str]:
        inputs = self.blip_processor(images=images, return_tensors="pt").to(self.device)
        with torch.no_grad():
            generated_ids = self.blip_model.generate(**inputs, max_new_tokens=50)

        captions = self.blip_processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )

        return captions
