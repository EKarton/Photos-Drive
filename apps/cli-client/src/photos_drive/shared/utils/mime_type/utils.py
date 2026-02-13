import magic


def is_image(mime_type: str) -> bool:
    '''
    Returns true if the file is an image based on its mime type; else false.

    Args:
        - mime_type (str): The mime type of the image
    '''
    return mime_type.startswith("image/")


def get_mime_type(file_path: str) -> str:
    '''
        Returns the mime type of the file.
    s
        Args:
            - file_path (str): The path to the file
    '''
    return magic.from_file(file_path, mime=True)
