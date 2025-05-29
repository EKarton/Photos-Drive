from bson.objectid import ObjectId


from dataclasses import dataclass


@dataclass(frozen=True)
class AlbumId:
    """
    Represents the ID of a album in MongoDB.
    Since albums are distributed across different MongoDB clients, it consists of the
    MongoDB client ID and the object ID.

    Attributes:
        client_id (ObjectId): The ID of the Mongo DB client that it is saved under.
        object_id (ObjectId): The object ID of the document
    """

    client_id: ObjectId
    object_id: ObjectId


def parse_string_to_album_id(value: str) -> AlbumId:
    '''
    Parses and converts a string into an Album ID.

    Args:
        value (str): The string must be in this format: 'abc:123'

    Returns:
        AlbumId: The album ID.
    '''
    client_id, object_id = value.split(":")
    return AlbumId(ObjectId(client_id), ObjectId(object_id))


def album_id_to_string(album_id: AlbumId) -> str:
    '''
    Parses and converts an Album ID to a string.

    Args:
        album_id (AlbumId): The album ID.

    Returns:
        string: The album ID in string form.
    '''
    return f"{album_id.client_id}:{album_id.object_id}"
