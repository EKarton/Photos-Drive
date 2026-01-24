from typing import Any
from typing import cast
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
from photos_drive.shared.core.database.mongodb import (
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


class TestSyncCli(unittest.TestCase):
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

        # 3. Initialize repositories for assertion support
        self.albums_repo = MongoDBAlbumsRepository(
            self.mongodb_client_id, self.mock_mongo_client, self.mongodb_clients_repo
        )
        self.media_items_repo = MongoDBMediaItemsRepository(
            self.mongodb_client_id, self.mock_mongo_client, self.mongodb_clients_repo
        )
        # Create root album
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

        # 5. Apply patches
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
                "photos_drive.cli.commands.sync.OpenCLIPImageEmbeddings",
                return_value=FakeImageEmbedder(),
            ),
            patch(
                "photos_drive.cli.commands.sync.BlipImageCaptions",
                return_value=FakeImageCaptions(),
            ),
            patch(
                "photos_drive.cli.commands.sync.DistributedVectorStore",
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

    def test_sync_additions(self):
        runner = CliRunner()
        app = build_app()

        with runner.isolated_filesystem():
            # Create a local file that is NOT in MongoDB or GPhotos
            filename = "new_image.jpg"
            with open(filename, "wb") as f:
                f.write(b"new data")

            # Act
            result = runner.invoke(
                app,
                args=["sync", ".", "--config-file", self.config_file_path],
                input="y\n",
            )

            # Assert
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Media items created: 1", result.stdout)

            # Verify MongoDB has the item
            media_items_coll = self.mock_mongo_client["photos_drive"]["media_items"]
            self.assertEqual(media_items_coll.count_documents({}), 1)
            self.assertEqual(
                cast(Any, media_items_coll.find_one())["file_name"], filename
            )

    def test_sync_deletions(self):
        runner = CliRunner()
        app = build_app()

        with runner.isolated_filesystem():
            # Seed MongoDB and GPhotos with an item that is NOT local
            filename = "gone_locally.jpg"

            # GPhotos seed
            up = self.fake_gphotos_client.media_items().upload_photo(filename, filename)
            res = self.fake_gphotos_client.media_items().add_uploaded_photos_to_gphotos(
                [up]
            )
            g_id = res.newMediaItemResults[0].mediaItem.id

            # MongoDB seed
            self.media_items_repo.create_media_item(
                CreateMediaItemRequest(
                    file_name=filename,
                    file_hash=b"h1",
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
                ["sync", ".", "--config-file", self.config_file_path],
                input="y\n",
            )

            # Assert
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Media items deleted: 1", result.stdout)

            # Verify MongoDB is empty
            media_items_coll = self.mock_mongo_client["photos_drive"]["media_items"]
            self.assertEqual(media_items_coll.count_documents({}), 0)

    def test_sync_cancelled(self):
        runner = CliRunner()
        app = build_app()

        with runner.isolated_filesystem():
            filename = "new.jpg"
            with open(filename, "wb") as f:
                f.write(b"data")

            # Act
            result = runner.invoke(
                app,
                ["sync", ".", "--config-file", self.config_file_path],
                input="n\n",
            )

            # Assert
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Operation cancelled.", result.stdout)

            # Verify MongoDB still empty
            media_items_coll = self.mock_mongo_client["photos_drive"]["media_items"]
            self.assertEqual(media_items_coll.count_documents({}), 0)
