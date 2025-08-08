import base64
import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def pil_image_to_base64(image: Image.Image, format="JPEG") -> str:
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_base64
