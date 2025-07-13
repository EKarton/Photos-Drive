import unittest
from datetime import datetime
from bson.objectid import ObjectId
import mercantile

from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.mongodb.testing import create_mock_mongo_client
from photos_drive.shared.metadata.album_id import AlbumId, album_id_to_string
from photos_drive.shared.metadata.media_item_id import (
    MediaItemId,
    media_item_id_to_string,
)
from photos_drive.shared.metadata.media_items import MediaItem, GpsLocation
from photos_drive.shared.tiles.mongodb.tiles_repository_impl import (
    TilesRepositoryImpl,
    MAX_ZOOM_LEVEL,
)
from photos_drive.shared.tiles.tiles_repository import (
    GetMediaItemsInTileRequest,
    GetNumMediaItemsInTileRequest,
)

MONGO_CLIENT_ID_1 = ObjectId("5f50c31e8a7d4b1c9c9b0b1a")
MONGO_CLIENT_ID_2 = ObjectId("5f50c31e8a7d4b1c9c9b0b1b")

ALBUM_ID_1 = AlbumId(MONGO_CLIENT_ID_1, ObjectId("5f50c31e8a7d4b1c9c9b0b1c"))
MEDIA_ITEM_ID_1 = MediaItemId(MONGO_CLIENT_ID_1, ObjectId("5f50c31e8a7d4b1c9c9b0b1d"))


class TestTilesRepositoryImpl(unittest.TestCase):
    def setUp(self):
        self.mock_client_1 = create_mock_mongo_client()
        self.mock_client_2 = create_mock_mongo_client()

        self.mongo_clients_repo = MongoDbClientsRepository()
        self.mongo_clients_repo.add_mongodb_client(
            MONGO_CLIENT_ID_1, self.mock_client_1
        )
        self.mongo_clients_repo.add_mongodb_client(
            MONGO_CLIENT_ID_2, self.mock_client_2
        )

        self.repo = TilesRepositoryImpl(self.mongo_clients_repo)

    def test_add_media_item(self):
        media_item = make_media_item()
        self.repo.add_media_item(media_item)

        # Check that it is added in all levels
        for z in range(0, MAX_ZOOM_LEVEL + 1):
            tile = mercantile.tile(
                media_item.location.longitude, media_item.location.latitude, z
            )
            found = self.mock_client_1["photos_drive"]["tiles"].find_one(
                {
                    "x": tile.x,
                    "y": tile.y,
                    "z": tile.z,
                    "album_id": album_id_to_string(media_item.album_id),
                    "media_item_id": media_item_id_to_string(media_item.id),
                }
            )
            self.assertIsNotNone(found)

    def test_add_media_item_with_no_location(self):
        media_item = MediaItem(
            id=MEDIA_ITEM_ID_1,
            file_name="test.jpg",
            file_hash=b"1234",
            location=None,
            gphotos_client_id="gphotos_1",
            gphotos_media_item_id="gphotos_media_item_id_1",
            album_id=ALBUM_ID_1,
            width=800,
            height=600,
            date_taken=datetime(2020, 1, 1),
        )

        with self.assertRaises(ValueError):
            self.repo.add_media_item(media_item)
        found = self.mock_client_1["photos_drive"]["tiles"].find_one(
            {
                "album_id": album_id_to_string(ALBUM_ID_1),
                "media_item_id": media_item_id_to_string(MEDIA_ITEM_ID_1),
            }
        )
        self.assertIsNone(found)

    def test_add_media_item_with_no_space(self):
        mock_client = create_mock_mongo_client(1)

        mongo_clients_repo = MongoDbClientsRepository()
        mongo_clients_repo.add_mongodb_client(MONGO_CLIENT_ID_1, mock_client)
        repo = TilesRepositoryImpl(mongo_clients_repo)

        with self.assertRaises(ValueError):
            repo.add_media_item(make_media_item())
        found = self.mock_client_1["photos_drive"]["tiles"].find_one(
            {
                "album_id": album_id_to_string(ALBUM_ID_1),
                "media_item_id": media_item_id_to_string(MEDIA_ITEM_ID_1),
            }
        )
        self.assertIsNone(found)

    def test_remove_media_item(self):
        media_item = make_media_item()
        self.repo.add_media_item(media_item)

        self.repo.remove_media_item(media_item)

        # Check that it is deleted
        for z in range(0, MAX_ZOOM_LEVEL + 1):
            tile = mercantile.tile(
                media_item.location.longitude, media_item.location.latitude, z
            )
            found = self.mock_client_1["photos_drive"]["tiles"].find_one(
                {
                    "x": tile.x,
                    "y": tile.y,
                    "z": tile.z,
                    "album_id": album_id_to_string(media_item.album_id),
                    "media_item_id": media_item_id_to_string(media_item.id),
                }
            )
            self.assertIsNone(found)

    def test_remove_media_item_with_no_location(self):
        album_id = AlbumId(MONGO_CLIENT_ID_1, ObjectId())
        media_item_id = MediaItemId(MONGO_CLIENT_ID_1, ObjectId())
        media_item = MediaItem(
            id=media_item_id,
            file_name="test.jpg",
            file_hash=b"1234",
            location=None,
            gphotos_client_id=MONGO_CLIENT_ID_1,
            gphotos_media_item_id="gphotos_id",
            album_id=album_id,
            width=800,
            height=600,
            date_taken=datetime(2020, 1, 1),
        )

        with self.assertRaises(ValueError):
            self.repo.remove_media_item(media_item)

    def test_get_num_media_items_in_tile(self):
        media_item = make_media_item()
        self.repo.add_media_item(media_item)

        for z in range(0, MAX_ZOOM_LEVEL + 1):
            tile = mercantile.tile(
                media_item.location.longitude, media_item.location.latitude, z
            )

            num = self.repo.get_num_media_items_in_tile(
                GetNumMediaItemsInTileRequest(
                    x=tile.x, y=tile.y, z=tile.z, album_id=media_item.album_id
                )
            )
            self.assertEqual(num, 1)

    def test_get_num_media_items_in_tile_with_no_album(self):
        media_item = make_media_item()
        self.repo.add_media_item(media_item)

        for z in range(0, MAX_ZOOM_LEVEL + 1):
            tile = mercantile.tile(
                media_item.location.longitude, media_item.location.latitude, z
            )

            num = self.repo.get_num_media_items_in_tile(
                GetNumMediaItemsInTileRequest(
                    x=tile.x, y=tile.y, z=tile.z, album_id=None
                )
            )
            self.assertEqual(num, 0)

    def test_get_num_media_items_in_tile_with_multiple_clients(self):
        item1 = make_media_item(album_id=AlbumId(MONGO_CLIENT_ID_1, ObjectId()))
        item2 = make_media_item(album_id=AlbumId(MONGO_CLIENT_ID_2, ObjectId()))
        self.repo.add_media_item(item1)
        self.repo.add_media_item(item2)

        for item in [item1, item2]:
            for z in range(0, MAX_ZOOM_LEVEL + 1):
                tile = mercantile.tile(
                    item.location.longitude, item.location.latitude, z
                )
                req = GetNumMediaItemsInTileRequest(
                    x=tile.x, y=tile.y, z=tile.z, album_id=item.album_id
                )

                num = self.repo.get_num_media_items_in_tile(req)
                self.assertEqual(num, 1)

    def test_get_media_item_ids_in_tile(self):
        media_item = make_media_item()
        self.repo.add_media_item(media_item)

        for z in range(0, MAX_ZOOM_LEVEL + 1):
            tile = mercantile.tile(
                media_item.location.longitude, media_item.location.latitude, z
            )
            req = GetMediaItemsInTileRequest(
                x=tile.x, y=tile.y, z=tile.z, album_id=media_item.album_id, limit=10
            )
            ids = self.repo.get_media_item_ids_in_tile(req)

            self.assertEqual(len(ids), 1)
            self.assertEqual(ids[0], media_item.id)

    def test_get_media_item_ids_in_tile_with_limit(self):
        album_id = AlbumId(MONGO_CLIENT_ID_1, ObjectId())
        items = [make_media_item(album_id=album_id) for _ in range(5)]
        for item in items:
            self.repo.add_media_item(item)

        tile = mercantile.tile(
            items[0].location.longitude, items[0].location.latitude, 0
        )
        req = GetMediaItemsInTileRequest(
            x=tile.x, y=tile.y, z=tile.z, album_id=album_id, limit=3
        )

        ids = self.repo.get_media_item_ids_in_tile(req)
        self.assertEqual(len(ids), 3)

    def test_get_media_item_ids_in_tile_with_no_album_and_has_limit(self):
        media_item = make_media_item()
        self.repo.add_media_item(media_item)

        for z in range(0, MAX_ZOOM_LEVEL + 1):
            tile = mercantile.tile(
                media_item.location.longitude, media_item.location.latitude, z
            )
            req = GetMediaItemsInTileRequest(
                x=tile.x, y=tile.y, z=tile.z, album_id=None, limit=10
            )

            ids = self.repo.get_media_item_ids_in_tile(req)
            self.assertEqual(len(ids), 0)


def make_media_item(
    longitude: float = 10.0,
    latitude: float = 20.0,
    album_id: AlbumId = ALBUM_ID_1,
    media_item_id: MediaItemId = MEDIA_ITEM_ID_1,
) -> MediaItem:
    return MediaItem(
        id=media_item_id,
        file_name="test.jpg",
        file_hash=b"1234",
        location=GpsLocation(latitude=latitude, longitude=longitude),
        gphotos_client_id="gphotos_client_id_1",
        gphotos_media_item_id="gphotos_media_item_id_1",
        album_id=album_id,
        width=800,
        height=600,
        date_taken=datetime(2020, 1, 1),
    )
