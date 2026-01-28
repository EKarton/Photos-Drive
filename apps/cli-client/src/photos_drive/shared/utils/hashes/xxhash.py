import xxhash


def compute_file_hash(file_path: str) -> bytes:
    '''
    Computes the file hash using xxhash library.

    Args:
        file_path (str): The file path

    Returns:
        bytes: The file hash, in bytes.
    '''
    hash_obj = xxhash.xxh64()
    with open(file_path, 'rb') as file:
        while chunk := file.read(8192):
            hash_obj.update(chunk)
    return hash_obj.digest()
