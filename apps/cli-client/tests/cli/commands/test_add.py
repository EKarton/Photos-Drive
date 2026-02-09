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
from photos_drive.shared.core.databases.mongodb import (
    MongoDBClientsRepository,
)
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


class TestAddCli(unittest.TestCase):
    def setUp(self):
        # 1. Set up mock MongoDB
        self.mongodb_client_id = ObjectId()
        self.mock_mongo_client = create_mock_mongo_client(
            1000 * 1024 * 1024
        )  # 1GB free
        self.mongodb_clients_repo = MongoDBClientsRepository()
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

        # 3. Initialize repositories for assertions later
        self.albums_repo = MongoDBAlbumsRepository(
            self.mongodb_client_id, self.mock_mongo_client, self.mongodb_clients_repo
        )
        self.media_items_repo = MongoDBMediaItemsRepository(
            self.mongodb_client_id, self.mock_mongo_client, self.mongodb_clients_repo
        )
        # Create root album
        self.root_album = self.albums_repo.create_album("", None)

        # 4. Create temporary test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.image1_path = os.path.join(self.test_dir.name, "image1.jpg")
        with open(self.image1_path, "wb") as f:
            f.write(b"fake image data 1")

        self.sub_dir = os.path.join(self.test_dir.name, "Summer2025")
        os.makedirs(self.sub_dir)
        self.image2_path = os.path.join(self.sub_dir, "image2.png")
        with open(self.image2_path, "wb") as f:
            f.write(b"fake image data 2")

        # 5. Build fake config file
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
        self.exif_mock = MagicMock()
        self.exif_mock.__enter__.return_value = self.exif_mock
        self.exif_mock.get_tags.side_effect = lambda files, *args, **kwargs: [
            {"SourceFile": f} for f in files
        ]

        self.patchers = [
            patch.object(
                MongoDBClientsRepository,
                "build_from_config",
                return_value=self.mongodb_clients_repo,
            ),
            patch.object(
                GPhotosClientsRepository,
                "build_from_config",
                return_value=self.gphotos_clients_repo,
            ),
            patch(
                "photos_drive.cli.commands.add.OpenCLIPImageEmbeddings",
                return_value=FakeImageEmbedder(),
            ),
            patch(
                "photos_drive.cli.commands.add.BlipImageCaptions",
                return_value=FakeImageCaptions(),
            ),
            patch(
                "photos_drive.cli.commands.add.DistributedVectorStore",
                return_value=FakeVectorStore(),
            ),
            # Mocking magic to avoid libmagic dependency issues in some environments
            patch("magic.from_file", return_value="image/jpeg"),
            # Mocking PIL and ExifTool to avoid real file processing
            patch("PIL.Image.open", return_value=MagicMock()),
            patch(
                "photos_drive.backup.processed_diffs.get_width_height_of_image",
                return_value=(800, 600),
            ),
            patch(
                "photos_drive.backup.processed_diffs.ExifToolHelper",
                return_value=self.exif_mock,
            ),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()
        os.unlink(self.config_file_path)
        self.test_dir.cleanup()

    def test_add_single_file(self):
        runner = CliRunner()
        app = build_app()

        # Act
        result = runner.invoke(
            app,
            args=["add", self.image1_path, "--config-file", self.config_file_path],
            input="y\n",
        )

        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Items added: 1", result.stdout)

        # Verify MongoDB state
        media_items_coll = self.mock_mongo_client["photos_drive"]["media_items"]
        docs = list(media_items_coll.find({}))
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["file_name"], "image1.jpg")
        self.assertEqual(docs[0]["gphotos_client_id"], str(self.gphotos_client_id))

        # Verify Google Photos state
        gitems = self.fake_gphotos_client.media_items().search_for_media_items()
        self.assertEqual(len(gitems), 1)
        self.assertEqual(gitems[0].filename, "image1.jpg")

    def test_add_directory(self):
        runner = CliRunner()
        app = build_app()

        # Act
        result = runner.invoke(
            app,
            args=["add", self.test_dir.name, "--config-file", self.config_file_path],
            input="y\n",
        )

        # Assert
        self.assertEqual(result.exit_code, 0)
        # Note: get_media_file_paths_from_path will find both
        # image1.jpg and Summer2025/image2.png
        self.assertIn("Items added: 2", result.stdout)

        # Verify MongoDB state
        media_items_coll = self.mock_mongo_client["photos_drive"]["media_items"]
        docs = list(media_items_coll.find({}))
        self.assertEqual(len(docs), 2)
        filenames = {doc["file_name"] for doc in docs}
        self.assertIn("image1.jpg", filenames)
        self.assertIn("image2.png", filenames)

        # Verify Albums are created for subdirectories
        albums_coll = self.mock_mongo_client["photos_drive"]["albums"]
        album_docs = list(albums_coll.find({"name": "Summer2025"}))
        self.assertEqual(len(album_docs), 1)

        # Verify Google Photos state
        gitems = self.fake_gphotos_client.media_items().search_for_media_items()
        self.assertEqual(len(gitems), 2)

    def test_add_cancelled_by_user(self):
        with patch(
            "photos_drive.cli.commands.add.prompt_user_for_yes_no_answer",
            return_value=False,
        ):
            runner = CliRunner()
            app = build_app()

            # Act
            result = runner.invoke(
                app,
                args=["add", self.image1_path, "--config-file", self.config_file_path],
                input="n\n",
            )

            # Assert
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Operation cancelled.", result.stdout)

            # Verify no items added
            media_items_coll = self.mock_mongo_client["photos_drive"]["media_items"]
            self.assertEqual(media_items_coll.count_documents({}), 0)
