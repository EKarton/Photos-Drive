from PIL import Image
import cv2

Image.MAX_IMAGE_PIXELS = None


def get_width_height_of_video(file_path: str) -> tuple[int, int]:
    vidcap = cv2.VideoCapture(file_path)
    if not vidcap.isOpened():
        raise ValueError(f"Cannot open video file: {file_path}")
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vidcap.release()
    return width, height
