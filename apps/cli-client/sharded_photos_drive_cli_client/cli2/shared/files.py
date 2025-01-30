import os

from ...shared.gphotos.valid_file_extensions import MEDIA_ITEM_FILE_EXTENSIONS


def get_media_file_paths_from_path(path: str) -> list[str]:
    """
    Returns a list of file paths that are under a path.

    If the path points to a media item, it will return the file path of that media item.

    If a path points to a directory, it will return a list of file paths to all media
    items under that directory.

    Args:
        path (str): A generic path

    Raises:
        ValueError if the path does not exist

    Returns:
        list(str): A list of file paths of media items it found.
    """
    if os.path.isdir(path):
        return __get_media_file_paths_from_dir_path(path)

    if os.path.isfile(path):
        if not path.lower().endswith(MEDIA_ITEM_FILE_EXTENSIONS):
            raise ValueError(f"File {path} is not an image or video")

        return [path]

    raise ValueError(f"File {path} does not exist")


def __get_media_file_paths_from_dir_path(dir_path: str) -> list[str]:
    """
    Returns a list of file paths of media items that are under a directory.

    Args:
        dir_path (str): A directory path

    Returns:
        list(str): A list of file paths to all media items under that directory.
    """
    diffs = []

    for root, _, files in os.walk(dir_path):
        for file in files:
            if not file.lower().endswith(MEDIA_ITEM_FILE_EXTENSIONS):
                continue

            # Construct the relative path
            relative_path = os.path.join(".", os.path.relpath(os.path.join(root, file)))

            # Replace '\' with '/' for consistency (from Windows to Unix-based)
            formatted_path = relative_path.replace(os.sep, "/")

            diffs.append(formatted_path)

    return diffs
