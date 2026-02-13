from PIL import Image
import cv2

Image.MAX_IMAGE_PIXELS = None


def get_width_height_of_video(file_path: str) -> tuple[int, int]:
    '''
    Get the width and height of a video file.

    Args:
        file_path: Path to the video file

    Returns:
        Tuple of (width, height)
    '''
    vidcap = cv2.VideoCapture(file_path)
    if not vidcap.isOpened():
        raise ValueError(f"Cannot open video file: {file_path}")
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    rotation = int(vidcap.get(cv2.CAP_PROP_ORIENTATION_META))
    vidcap.release()

    rotation = rotation % 360
    if rotation in (90, 270):
        return (height, width)
    return (width, height)
