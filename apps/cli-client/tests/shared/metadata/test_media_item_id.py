import unittest
from bson.objectid import ObjectId

from photos_drive.shared.metadata.media_item_id import (
    MediaItemId,
    parse_string_to_media_item_id,
    media_item_id_to_string,
)


class MediaItemIdToStringTests(unittest.TestCase):
    def test_media_item_id_to_string(self):
        client_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1a")
        object_id = ObjectId("5f50c31e8a7d4b1c9c9b0b1b")
        media_id = MediaItemId(client_id=client_id, object_id=object_id)

        result = media_item_id_to_string(media_id)

        self.assertEqual(result, "5f50c31e8a7d4b1c9c9b0b1a:5f50c31e8a7d4b1c9c9b0b1b")


class ParseStringToMediaItemIdTests(unittest.TestCase):
    def test_parse_string_to_media_item_id(self):
        input_str = "5f50c31e8a7d4b1c9c9b0b1a:5f50c31e8a7d4b1c9c9b0b1b"
        result = parse_string_to_media_item_id(input_str)

        self.assertEqual(result.client_id, ObjectId("5f50c31e8a7d4b1c9c9b0b1a"))
        self.assertEqual(result.object_id, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))


class MediaItemIdTests(unittest.TestCase):
    def test_media_item_id_equality(self):
        client_id = ObjectId()
        object_id = ObjectId()
        media_id1 = MediaItemId(client_id=client_id, object_id=object_id)
        media_id2 = MediaItemId(client_id=client_id, object_id=object_id)

        self.assertEqual(media_id1, media_id2)
        self.assertTrue(media_id1 == media_id2)
        self.assertEqual(hash(media_id1), hash(media_id2))
