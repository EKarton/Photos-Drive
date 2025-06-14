import cv2


def get_width_height_of_video(file_path: str) -> tuple[int, int]:
    vidcap = cv2.VideoCapture(file_path)
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return width, height
