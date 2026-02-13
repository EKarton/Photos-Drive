from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()


def get_width_height_of_image(file_path: str) -> tuple[int, int]:
    '''
    Get the width and height of an image file.

    Args:
        file_path: Path to the image file

    Returns:
        Tuple of (width, height)
    '''
    with Image.open(file_path) as image:
        return ImageOps.exif_transpose(image).size
