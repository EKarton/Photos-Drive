from pillow_heif import register_heif_opener
from PIL import Image

register_heif_opener()


def get_width_height_of_image(file_path: str) -> tuple[int, int]:
    with Image.open(file_path) as image:
        return image.size
