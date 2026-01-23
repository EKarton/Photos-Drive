import unittest

from bson.objectid import ObjectId

from photos_drive.shared.core.metadata.albums.album_id import (
    AlbumId,
    album_id_to_string,
    parse_string_to_album_id,
)


class ParseStringToAlbumIdTests(unittest.TestCase):
    def test_parse_string_to_album_id__valid(self):
        client_id = ObjectId()
        object_id = ObjectId()
        album_id_string = f"{client_id}:{object_id}"

        album_id = parse_string_to_album_id(album_id_string)

        self.assertEqual(album_id.client_id, client_id)
        self.assertEqual(album_id.object_id, object_id)


class AlbumIdToStringTests(unittest.TestCase):
    def test_album_id_to_string__valid(self):
        client_id = ObjectId()
        object_id = ObjectId()
        album_id = AlbumId(client_id=client_id, object_id=object_id)

        album_id_string = album_id_to_string(album_id)

        self.assertEqual(album_id_string, f"{client_id}:{object_id}")
