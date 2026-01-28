def is_image(mime_type: str) -> bool:
    '''
    Returns true if the file is an image based on its mime type; else false.

    Args:
        - mime_type (str): The mime type of the image
    '''
    return mime_type.startswith("image/")
