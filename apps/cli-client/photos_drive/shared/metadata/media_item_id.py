from bson.objectid import ObjectId


from dataclasses import dataclass


@dataclass(frozen=True)
class MediaItemId:
    """
    Represents the ID of a media item in MongoDB.
    Since media items are distributed across different MongoDB clients, it consists of
    the MongoDB client ID and the object ID.

    Attributes:
        client_id (ObjectId): The ID of the Mongo DB client that it is saved under.
        object_id (ObjectId): The object ID of the document
    """

    client_id: ObjectId
    object_id: ObjectId


def parse_string_to_media_item_id(value: str) -> MediaItemId:
    '''
    Parses and converts a string into a Media Item ID.

    Args:
        value (str): The string must be in this format: 'abc:123'

    Returns:
        MediaItemId: The media item ID.
    '''
    client_id, object_id = value.split(":")
    return MediaItemId(ObjectId(client_id), ObjectId(object_id))


def media_item_id_to_string(media_item_id: MediaItemId) -> str:
    '''
    Parses and converts a Media Item ID to a string.

    Args:
        media_item_id (MediaItemId): The media item ID.

    Returns:
        string: The media item ID in string form.
    '''
    return f"{media_item_id.client_id}:{media_item_id.object_id}"
