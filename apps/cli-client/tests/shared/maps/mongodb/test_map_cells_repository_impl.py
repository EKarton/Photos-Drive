from datetime import datetime
import unittest
from bson import ObjectId

from photos_drive.shared.maps.mongodb.map_cells_repository_impl import (
    MapCellsRepositoryImpl,
    MAX_CELL_RESOLUTION,
)
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.mongodb.testing import create_mock_mongo_client
from photos_drive.shared.metadata.album_id import AlbumId, album_id_to_string
from photos_drive.shared.metadata.media_item_id import (
    MediaItemId,
    media_item_id_to_string,
)
from photos_drive.shared.metadata.media_items import MediaItem
from photos_drive.shared.metadata.gps_location import GpsLocation


MONGO_CLIENT_ID = ObjectId("5f50c31e8a7d4b1c9c9b0b1a")

ALBUM_ID = AlbumId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1b"))

MEDIA_ITEM_ID = MediaItemId(MONGO_CLIENT_ID, ObjectId("5f50c31e8a7d4b1c9c9b0b1c"))

FILE_HASH = b'\x8a\x19\xdd\xdeg\xdd\x96\xf2'

MEDIA_ITEM = MediaItem(
    id=MEDIA_ITEM_ID,
    file_name="photo.jpg",
    location=GpsLocation(latitude=37.7749, longitude=-122.4194),  # San Francisco
    file_hash=FILE_HASH,
    gphotos_media_item_id="gphotos:media1",
    gphotos_client_id=ObjectId(),
    album_id=ALBUM_ID,
    width=4000,
    height=3000,
    date_taken=datetime(2026, 1, 1, 14, 30, 0),
    embedding_id=None,
)


class TestMapCellsRepositoryImpl(unittest.TestCase):

    def setUp(self):
        self.mongo_client = create_mock_mongo_client()
        self.clients_repo = MongoDbClientsRepository()
        self.clients_repo.add_mongodb_client(MONGO_CLIENT_ID, self.mongo_client)
        self.repo = MapCellsRepositoryImpl(self.clients_repo)

    def test_add_media_item__inserts_cells_at_all_resolutions(self):
        self.repo.add_media_item(MEDIA_ITEM)

        map_cells_coll = self.mongo_client["photos_drive"]["map_cells"]
        cells = list(map_cells_coll.find())

        self.assertEqual(len(cells), MAX_CELL_RESOLUTION + 1)  # res 0 to 15
        for cell in cells:
            self.assertEqual(cell["album_id"], album_id_to_string(ALBUM_ID))
            self.assertEqual(
                cell["media_item_id"], media_item_id_to_string(MEDIA_ITEM_ID)
            )
            self.assertIsNotNone(cell["cell_id"])

    def test_add_media_item_on_no_available_mongodb_client(self):
        mongo_client = create_mock_mongo_client(total_free_storage_size=-1)
        clients_repo = MongoDbClientsRepository()
        clients_repo.add_mongodb_client(MONGO_CLIENT_ID, mongo_client)
        repo = MapCellsRepositoryImpl(clients_repo)

        with self.assertRaises(ValueError) as context:
            repo.add_media_item(MEDIA_ITEM)
        self.assertIn(
            "Unable to find space to insert h3 map cells", str(context.exception)
        )

    def test_add_media_item__raises_with_no_location(self):
        media_item = MediaItem(
            id=MEDIA_ITEM_ID,
            file_name="photo.jpg",
            location=None,
            file_hash=FILE_HASH,
            gphotos_media_item_id="gphotos:media1",
            gphotos_client_id=ObjectId(),
            album_id=ALBUM_ID,
            width=4000,
            height=3000,
            date_taken=datetime(2026, 1, 1, 14, 30, 0),
            embedding_id=None,
        )

        with self.assertRaises(ValueError) as context:
            self.repo.add_media_item(media_item)
        self.assertIn("No gps location", str(context.exception))

    def test_remove_media_item__deletes_all_cells(self):
        # First, add the media item
        self.repo.add_media_item(MEDIA_ITEM)

        # Ensure cells are present
        inserted = list(self.mongo_client["photos_drive"]["map_cells"].find())
        self.assertGreater(len(inserted), 0)

        # Now, remove the media item
        self.repo.remove_media_item(MEDIA_ITEM.id)

        # Check that cells were deleted
        deleted = list(self.mongo_client["photos_drive"]["map_cells"].find())
        self.assertEqual(len(deleted), 0)
