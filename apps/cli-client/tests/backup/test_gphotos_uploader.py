import unittest
from bson.objectid import ObjectId

from sharded_photos_drive_cli_client.shared.gphotos.testing import (
    FakeItemsRepository,
    FakeGPhotosClient,
)
from sharded_photos_drive_cli_client.backup.gphotos_uploader import (
    GPhotosMediaItemUploader,
    UploadRequest,
)
from sharded_photos_drive_cli_client.shared.gphotos.clients_repository import (
    GPhotosClientsRepository,
)


class TestGPhotosMediaItemUploader(unittest.TestCase):
    def test_upload_photos_success(self):
        gphotos_client_id = ObjectId()
        gphotos_client_id_str = str(gphotos_client_id)
        gphotos_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_repo, gphotos_client_id_str)
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        uploader = GPhotosMediaItemUploader(gphotos_clients_repo)

        upload_requests = [
            UploadRequest(
                file_path="path/to/photo1.jpg",
                file_name="photo1.jpg",
                gphotos_client_id=gphotos_client_id,
            ),
            UploadRequest(
                file_path="path/to/photo2.jpg",
                file_name="photo2.jpg",
                gphotos_client_id=gphotos_client_id,
            ),
        ]

        media_item_ids = uploader.upload_photos(upload_requests)

        stored_media_items = gphotos_repo.search_for_media_items(
            client_id=gphotos_client_id_str
        )
        self.assertEqual(len(stored_media_items), len(media_item_ids))
        self.assertEqual(stored_media_items[0].id, media_item_ids[0])
        self.assertEqual(stored_media_items[1].id, media_item_ids[1])
