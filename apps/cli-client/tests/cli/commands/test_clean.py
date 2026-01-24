import os
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import tempfile
from bson import ObjectId
from typer.testing import CliRunner

from photos_drive.cli.app import build_app
from photos_drive.shared.core.albums.repository.mongodb import (
    MongoDBAlbumsRepository,
)
from photos_drive.shared.core.clients.mongodb import (
    MongoDbClientsRepository,
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

MOCK_DATE_TAKEN = datetime(2025, 6, 6, 14, 30, 0, tzinfo=timezone.utc)


class TestCleanCli(unittest.TestCase):
    def setUp(self):
        # 1. Set up mock MongoDB and GPhotos environments
        self.mongodb_client_id = ObjectId()
        self.mock_mongo_client = create_mock_mongo_client(1000 * 1024 * 1024)
        self.mongodb_clients_repo = MongoDbClientsRepository()
        self.mongodb_clients_repo.add_mongodb_client(
            self.mongodb_client_id, self.mock_mongo_client
        )

        self.gphotos_client_id = ObjectId()
        self.fake_gitems_repo = FakeItemsRepository()
        self.fake_gphotos_client = FakeGPhotosClient(
            self.fake_gitems_repo, "test@gmail.com"
        )
        self.gphotos_clients_repo = GPhotosClientsRepository()
        self.gphotos_clients_repo.add_gphotos_client(
            self.gphotos_client_id, self.fake_gphotos_client
        )

        # 2. Initialize repositories for seeding
        self.albums_repo = MongoDBAlbumsRepository(
            self.mongodb_client_id, self.mongodb_clients_repo
        )
        self.media_items_repo = MongoDBMediaItemsRepository(
            self.mongodb_client_id, self.mongodb_clients_repo
        )
        # Create root album (linked to config)
        self.root_album = self.albums_repo.create_album("", None)

        # 3. Build fake config file
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

        # 4. Apply global patches
        self.patchers = [
            patch.object(
                MongoDbClientsRepository,
                "build_from_config",
                return_value=self.mongodb_clients_repo,
            ),
            patch.object(
                GPhotosClientsRepository,
                "build_from_config",
                return_value=self.gphotos_clients_repo,
            ),
            patch(
                "photos_drive.cli.commands.clean.prompt_user_for_yes_no_answer",
                return_value=True,
            ),
            patch("magic.from_file", return_value="image/jpeg"),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()
        self.config_dir.cleanup()

    def test_clean_orphaned_albums_and_items(self):
        # 1. Seed reachables
        reachable_album = self.albums_repo.create_album("Reachable", self.root_album.id)

        # 2. Seed orphaned data (unlinked from root BFS)
        unreachable_album = self.albums_repo.create_album("Orphan", None)

        # Unreachable GPhotos item
        up = self.fake_gphotos_client.media_items().upload_photo("orph.jpg", "orph.jpg")
        res = self.fake_gphotos_client.media_items().add_uploaded_photos_to_gphotos(
            [up]
        )
        orph_g_id = res.newMediaItemResults[0].mediaItem.id

        # Reachable GPhotos item (metadata exists in DB linked to root)
        up_ok = self.fake_gphotos_client.media_items().upload_photo("ok.jpg", "ok.jpg")
        res_ok = self.fake_gphotos_client.media_items().add_uploaded_photos_to_gphotos(
            [up_ok]
        )
        ok_g_id = res_ok.newMediaItemResults[0].mediaItem.id

        self.media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name="ok.jpg",
                file_hash=b"h1",
                location=None,
                gphotos_client_id=self.gphotos_client_id,
                gphotos_media_item_id=ok_g_id,
                album_id=reachable_album.id,
                width=100,
                height=100,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # 3. Seed unreferenced media item in DB (GPhotos ID doesn't exist anymore or just unlinked)
        # Actually SystemCleaner checks reachable Gmedia items.
        # If reachable DB item's Gmedia ID is NOT in GPhotos, it might fail or just keep it?
        # SystemCleaner.__find_content_to_keep filters items whose gphotos_media_item_id is not in all_gphoto_media_item_ids.

        runner = CliRunner()
        app = build_app()

        # Act
        result = runner.invoke(
            app, args=["clean", "--config-file", self.config_file_path]
        )

        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Cleanup success!", result.stdout)

        # Verify orphaned album deleted
        self.assertEqual(
            self.mock_mongo_client["photos_drive"]["albums"].count_documents(
                {"name": "Orphan"}
            ),
            0,
        )
        # Verify reachable album kept
        self.assertEqual(
            self.mock_mongo_client["photos_drive"]["albums"].count_documents(
                {"name": "Reachable"}
            ),
            1,
        )

        # Verify unreferenced GPhotos item moved to trash
        albums = self.fake_gphotos_client.albums().list_albums()
        trash_album = next(a for a in albums if a.title == "To delete")
        media_in_trash = self.fake_gphotos_client.media_items().search_for_media_items(
            trash_album.id
        )
        self.assertEqual(len(media_in_trash), 1)
        self.assertEqual(media_in_trash[0].id, orph_g_id)

    def test_clean_cancelled(self):
        with patch(
            "photos_drive.cli.commands.clean.prompt_user_for_yes_no_answer",
            return_value=False,
        ):
            # Seed unreachable album
            self.albums_repo.create_album("Orphan", None)

            runner = CliRunner()
            app = build_app()

            # Act
            result = runner.invoke(
                app, args=["clean", "--config-file", self.config_file_path]
            )

            # Assert
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Operation cancelled.", result.stdout)
            # Album should still exist
            self.assertEqual(
                self.mock_mongo_client["photos_drive"]["albums"].count_documents(
                    {"name": "Orphan"}
                ),
                1,
            )

    def test_clean_nothing_to_do(self):
        # Only reachable items
        reachable_album = self.albums_repo.create_album("Reachable", self.root_album.id)
        up = self.fake_gphotos_client.media_items().upload_photo("ok.jpg", "ok.jpg")
        res = self.fake_gphotos_client.media_items().add_uploaded_photos_to_gphotos(
            [up]
        )

        self.media_items_repo.create_media_item(
            CreateMediaItemRequest(
                file_name="ok.jpg",
                file_hash=b"h1",
                location=None,
                gphotos_client_id=self.gphotos_client_id,
                gphotos_media_item_id=res.newMediaItemResults[0].mediaItem.id,
                album_id=reachable_album.id,
                width=100,
                height=100,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        runner = CliRunner()
        app = build_app()

        # Act
        result = runner.invoke(
            app, args=["clean", "--config-file", self.config_file_path]
        )

        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Number of media items deleted: 0", result.stdout)
        self.assertIn("Number of albums deleted: 0", result.stdout)
        self.assertIn("Number of Google Photos items trashed: 0", result.stdout)
