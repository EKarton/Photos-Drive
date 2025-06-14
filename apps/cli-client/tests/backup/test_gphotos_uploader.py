import unittest
from bson.objectid import ObjectId

from photos_drive.shared.blob_store.gphotos.testing import (
    FakeItemsRepository,
    FakeGPhotosClient,
)
from photos_drive.backup.gphotos_uploader import (
    GPhotosMediaItemParallelUploaderImpl,
    GPhotosMediaItemUploaderImpl,
    UploadRequest,
)
from photos_drive.shared.blob_store.gphotos.clients_repository import (
    GPhotosClientsRepository,
)


class TestGPhotosMediaItemUploaderImpl(unittest.TestCase):
    def test_upload_photos_success(self):
        gphotos_client_id = ObjectId()
        gphotos_client_id_str = str(gphotos_client_id)
        gphotos_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_repo, gphotos_client_id_str)
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        uploader = GPhotosMediaItemUploaderImpl(gphotos_clients_repo)

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


class TestGPhotosMediaItemParallelUploaderImpl(unittest.TestCase):
    def test_upload_photos_success(self):
        gphotos_client_id = ObjectId()
        gphotos_client_id_str = str(gphotos_client_id)
        gphotos_repo = FakeItemsRepository()
        gphotos_client = FakeGPhotosClient(gphotos_repo, gphotos_client_id_str)
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id, gphotos_client)
        uploader = GPhotosMediaItemParallelUploaderImpl(gphotos_clients_repo)

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
        self.assertNotEqual(stored_media_items[0].id, stored_media_items[1].id)
        self.assertTrue(stored_media_items[0].id in media_item_ids)
        self.assertTrue(stored_media_items[1].id in media_item_ids)

    def test_upload_photos_multiple_clients_success(self):
        gphotos_client_id_1 = ObjectId()
        gphotos_client_id_1_str = str(gphotos_client_id_1)
        gphotos_client_id_2 = ObjectId()
        gphotos_client_id_2_str = str(gphotos_client_id_2)
        gphotos_repo = FakeItemsRepository()
        gphotos_client_1 = FakeGPhotosClient(gphotos_repo, gphotos_client_id_1_str)
        gphotos_client_2 = FakeGPhotosClient(gphotos_repo, gphotos_client_id_2_str)
        gphotos_clients_repo = GPhotosClientsRepository()
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id_1, gphotos_client_1)
        gphotos_clients_repo.add_gphotos_client(gphotos_client_id_2, gphotos_client_2)
        uploader = GPhotosMediaItemParallelUploaderImpl(gphotos_clients_repo)

        upload_requests = [
            UploadRequest(
                file_path="path/to/photo1.jpg",
                file_name="photo1.jpg",
                gphotos_client_id=gphotos_client_id_1,
            ),
            UploadRequest(
                file_path="path/to/photo2.jpg",
                file_name="photo2.jpg",
                gphotos_client_id=gphotos_client_id_2,
            ),
        ]

        media_item_ids = uploader.upload_photos(upload_requests)

        stored_media_items_1 = gphotos_repo.search_for_media_items(
            client_id=gphotos_client_id_1_str
        )
        stored_media_items_2 = gphotos_repo.search_for_media_items(
            client_id=gphotos_client_id_2_str
        )
        self.assertEqual(len(stored_media_items_1), 1)
        self.assertEqual(len(stored_media_items_2), 1)
        self.assertEqual(stored_media_items_1[0].id, media_item_ids[0])
        self.assertEqual(stored_media_items_2[0].id, media_item_ids[1])
