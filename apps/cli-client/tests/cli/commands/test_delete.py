from datetime import datetime
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId
from typer.testing import CliRunner

from photos_drive.cli.app import build_app
from photos_drive.shared.core.albums.repository.mongodb import (
    MongoDBAlbumsRepository,
)
from photos_drive.shared.core.clients.mongodb import (
    MongoDbTransactionRepository,
)
from photos_drive.shared.core.media_items.repository.base import CreateMediaItemRequest
from photos_drive.shared.core.media_items.repository.mongodb import (
    MongoDBMediaItemsRepository,
)
from photos_drive.shared.core.storage.gphotos.clients_repository import (
    GPhotosClientsRepository,
)
from photos_drive.shared.core.storage.gphotos.testing import (
    FakeGPhotosClient,
    FakeItemsRepository,
)
from photos_drive.shared.core.testing.mock_mongo_client import (
    create_mock_mongo_client,
)
from photos_drive.shared.features.llm.models.testing.fake_image_captions import (
    FakeImageCaptions,
)
from photos_drive.shared.features.llm.models.testing.fake_image_embedder import (
    FakeImageEmbedder,
)
from photos_drive.shared.features.llm.vector_stores.testing.fake_vector_store import (
    FakeVectorStore,
)


class TestDeleteCli(unittest.TestCase):
    def setUp(self):
        # 1. Set up mock MongoDB
        self.mongodb_client_id = ObjectId()
        self.mock_mongo_client = create_mock_mongo_client(
            1000 * 1024 * 1024
        )  # 1GB free
        self.mongodb_clients_repo = MongoDbTransactionRepository()
        self.mongodb_clients_repo.add_mongodb_client(
            self.mongodb_client_id, self.mock_mongo_client
        )

        # 2. Set up fake Google Photos
        self.gphotos_client_id = ObjectId()
        self.fake_gitems_repo = FakeItemsRepository()
        self.fake_gphotos_client = FakeGPhotosClient(
            self.fake_gitems_repo, "test@gmail.com"
        )
        self.gphotos_clients_repo = GPhotosClientsRepository()
        self.gphotos_clients_repo.add_gphotos_client(
            self.gphotos_client_id, self.fake_gphotos_client
        )

        # 3. Initialize repositories
        self.albums_repo = MongoDBAlbumsRepository(
            self.mongodb_client_id, self.mock_mongo_client, self.mongodb_clients_repo
        )
        self.media_items_repo = MongoDBMediaItemsRepository(
            self.mongodb_client_id, self.mongodb_clients_repo
        )
        # Create root album (name is "")
        self.root_album = self.albums_repo.create_album("", None)

        # 4. Build fake config file
        self.config_dir = tempfile.TemporaryDirectory()
        self.config_file_path = os.path.join(self.config_dir.name, "config.ini")
        with open(self.config_file_path, "w") as f:
            f.write(
                f"[{self.mongodb_client_id}]\n"
                + "type = mongodb_config\n"
                + "name = TestMongoDB\n"
                + "read_write_connection_string = mongodb://localhost:27017\n"
                + "read_only_connection_string = mongodb://localhost:27016\n"
                + "\n"
                + f"[{self.gphotos_client_id}]\n"
                + "type = gphotos_config\n"
                + "name = TestGPhotos\n"
                + "read_write_token = test_token\n"
                + "read_write_refresh_token = test_refresh_token\n"
                + "read_write_client_id = test_client_id\n"
                + "read_write_client_secret = test_client_secret\n"
                + "read_write_token_uri = https://oauth2.googleapis.com/token\n"
                + "read_only_token = test_token_2\n"
                + "read_only_refresh_token = test_refresh_token_2\n"
                + "read_only_client_id = test_client_id_2\n"
                + "read_only_client_secret = test_client_secret_2\n"
                + "read_only_token_uri = https://oauth2.googleapis.com/token\n"
                + "\n"
                + f"[{ObjectId()}]\n"
                + "type = root_album\n"
                + f"client_id = {self.root_album.id.client_id}\n"
                + f"object_id = {self.root_album.id.object_id}\n"
                + "\n"
                + f"[{ObjectId()}]\n"
                + "type = vector_store_config\n"
                + "name = TestVectorStore\n"
                + "path = memory\n"
            )

        # 6. Apply patches
        self.patchers = [
            patch.object(
                MongoDbTransactionRepository,
                "build_from_config",
                return_value=self.mongodb_clients_repo,
            ),
            patch.object(
                GPhotosClientsRepository,
                "build_from_config",
                return_value=self.gphotos_clients_repo,
            ),
            patch(
                "photos_drive.cli.commands.delete.OpenCLIPImageEmbeddings",
                return_value=FakeImageEmbedder(),
            ),
            patch(
                "photos_drive.cli.commands.delete.BlipImageCaptions",
                return_value=FakeImageCaptions(),
            ),
            patch(
                "photos_drive.cli.commands.delete.DistributedVectorStore",
                return_value=FakeVectorStore(),
            ),
            patch("magic.from_file", return_value="image/jpeg"),
            patch("PIL.Image.open", return_value=MagicMock()),
            patch(
                "photos_drive.backup.processed_diffs.get_width_height_of_image",
                return_value=(800, 600),
            ),
            patch(
                "photos_drive.backup.processed_diffs.ExifToolHelper",
                return_value=MagicMock(),
            ),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()
        self.config_dir.cleanup()

    def test_delete_single_file(self):
        runner = CliRunner()
        app = build_app()

        with runner.isolated_filesystem():
            # 1. Create file locally (so get_media_file_paths_from_path finds it)
            filename = "image1.jpg"
            with open(filename, "wb") as f:
                f.write(b"fake data")

            # 2. Seed GPhotos with this file
            up = self.fake_gphotos_client.media_items().upload_photo(filename, filename)
            res = self.fake_gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [up]
            )
            g_id = res.newMediaItemResults[0].mediaItem.id

            # 3. Seed MongoDB (Album "" is root)
            self.media_items_repo.create_media_item(
                CreateMediaItemRequest(
                    file_name=filename,
                    file_hash=b"hash1",
                    location=None,
                    gphotos_client_id=self.gphotos_client_id,
                    gphotos_media_item_id=g_id,
                    album_id=self.root_album.id,
                    width=800,
                    height=600,
                    date_taken=datetime(2025, 1, 1),
                    embedding_id=None,
                )
            )

            # Act
            result = runner.invoke(
                app,
                args=["delete", filename, "--config-file", self.config_file_path],
                input="y\n",
            )

            # Assert
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Items deleted: 1", result.stdout)

            # Verify MongoDB state
            media_items_coll = self.mock_mongo_client["photos_drive"]["media_items"]
            self.assertEqual(media_items_coll.count_documents({}), 0)

    def test_delete_directory(self):
        runner = CliRunner()
        app = build_app()

        with runner.isolated_filesystem():
            # 1. Create directory structure and files
            os.makedirs("Summer")
            file1 = "image1.jpg"
            file2 = "Summer/image2.png"
            with open(file1, "wb") as f:
                f.write(b"d1")
            with open(file2, "wb") as f:
                f.write(b"d2")

            # 2. Seed GPhotos
            up1 = self.fake_gphotos_client.media_items().upload_photo(
                file1, "image1.jpg"
            )
            res1 = (
                self.fake_gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                    [up1]
                )
            )
            up2 = self.fake_gphotos_client.media_items().upload_photo(
                file2, "image2.png"
            )
            res2 = (
                self.fake_gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                    [up2]
                )
            )

            # 3. Seed MongoDB
            # Root file (album "")
            self.media_items_repo.create_media_item(
                CreateMediaItemRequest(
                    file_name="image1.jpg",
                    file_hash=b"h1",
                    location=None,
                    gphotos_client_id=self.gphotos_client_id,
                    gphotos_media_item_id=res1.newMediaItemResults[0].mediaItem.id,
                    album_id=self.root_album.id,
                    width=800,
                    height=600,
                    date_taken=datetime(2025, 1, 1),
                    embedding_id=None,
                )
            )
            # Subdir file (album "Summer")
            summer_album = self.albums_repo.create_album("Summer", self.root_album.id)
            self.media_items_repo.create_media_item(
                CreateMediaItemRequest(
                    file_name="image2.png",
                    file_hash=b"h2",
                    location=None,
                    gphotos_client_id=self.gphotos_client_id,
                    gphotos_media_item_id=res2.newMediaItemResults[0].mediaItem.id,
                    album_id=summer_album.id,
                    width=800,
                    height=600,
                    date_taken=datetime(2025, 1, 1),
                    embedding_id=None,
                )
            )

            # Act
            # "delete ." will find everything under the isolated FS root
            result = runner.invoke(
                app,
                args=["delete", ".", "--config-file", self.config_file_path],
                input="y\n",
            )

            # Assert
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Items deleted: 2", result.stdout)

            # Verify MongoDB state
            media_items_coll = self.mock_mongo_client["photos_drive"]["media_items"]
            self.assertEqual(media_items_coll.count_documents({}), 0)

            # Verify Album pruned
            albums_coll = self.mock_mongo_client["photos_drive"]["albums"]
            self.assertEqual(albums_coll.count_documents({"name": "Summer"}), 0)

    def test_delete_cancelled_by_user(self):
        runner = CliRunner()
        app = build_app()

        with runner.isolated_filesystem():
            filename = "image1.jpg"
            with open(filename, "wb") as f:
                f.write(b"d")

            self.media_items_repo.create_media_item(
                CreateMediaItemRequest(
                    file_name=filename,
                    file_hash=b"h",
                    location=None,
                    gphotos_client_id=self.gphotos_client_id,
                    gphotos_media_item_id="some_id",
                    album_id=self.root_album.id,
                    width=800,
                    height=600,
                    date_taken=datetime(2025, 1, 1),
                    embedding_id=None,
                )
            )

            # Act
            result = runner.invoke(
                app,
                args=["delete", filename, "--config-file", self.config_file_path],
                input="n\n",
            )

            # Assert
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Operation cancelled.", result.stdout)

            # Verify no items deleted
            media_items_coll = self.mock_mongo_client["photos_drive"]["media_items"]
            self.assertEqual(media_items_coll.count_documents({}), 1)
