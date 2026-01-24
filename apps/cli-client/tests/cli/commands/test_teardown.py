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


class TestTeardownCli(unittest.TestCase):
    def setUp(self):
        # 1. Set up mock MongoDB and GPhotos environments
        # Client 1
        self.mongodb_client_id_1 = ObjectId()
        self.mock_mongo_client_1 = create_mock_mongo_client(1000)
        self.gphotos_client_id_1 = ObjectId()
        self.fake_gitems_repo_1 = FakeItemsRepository()
        self.fake_gphotos_client_1 = FakeGPhotosClient(
            self.fake_gitems_repo_1, "client1@gmail.com"
        )

        # Client 2
        self.mongodb_client_id_2 = ObjectId()
        self.mock_mongo_client_2 = create_mock_mongo_client(1000)
        self.gphotos_client_id_2 = ObjectId()
        self.fake_gitems_repo_2 = FakeItemsRepository()
        self.fake_gphotos_client_2 = FakeGPhotosClient(
            self.fake_gitems_repo_2, "client2@gmail.com"
        )

        self.mongodb_clients_repo = MongoDbClientsRepository()
        self.mongodb_clients_repo.add_mongodb_client(
            self.mongodb_client_id_1, self.mock_mongo_client_1
        )
        self.mongodb_clients_repo.add_mongodb_client(
            self.mongodb_client_id_2, self.mock_mongo_client_2
        )

        self.gphotos_clients_repo = GPhotosClientsRepository()
        self.gphotos_clients_repo.add_gphotos_client(
            self.gphotos_client_id_1, self.fake_gphotos_client_1
        )
        self.gphotos_clients_repo.add_gphotos_client(
            self.gphotos_client_id_2, self.fake_gphotos_client_2
        )

        # 2. Initialize repositories for seeding
        self.albums_repo_1 = MongoDBAlbumsRepository(
            self.mongodb_client_id_1, self.mongodb_clients_repo
        )
        self.media_items_repo_1 = MongoDBMediaItemsRepository(
            self.mongodb_client_id_1, self.mongodb_clients_repo
        )

        # Create root album for Client 1
        self.root_album_1 = self.albums_repo_1.create_album("", None)

        # 3. Build fake config file
        self.config_dir = tempfile.TemporaryDirectory()
        self.config_file_path = os.path.join(self.config_dir.name, "config.ini")
        with open(self.config_file_path, "w") as f:
            f.write(
                f"[{self.mongodb_client_id_1}]\n"
                + "type = mongodb_config\n"
                + "name = Client1DB\n"
                + "read_write_connection_string = mongodb://localhost:27017\n"
                + "read_only_connection_string = mongodb://localhost:27016\n"
                + "\n"
                + f"[{self.gphotos_client_id_1}]\n"
                + "type = gphotos_config\n"
                + "name = Client1GP\n"
                + "read_write_token = t1\n"
                + "read_write_refresh_token = r1\n"
                + "read_write_client_id = id1\n"
                + "read_write_client_secret = s1\n"
                + "read_write_token_uri = https://oauth2.googleapis.com/token\n"
                + "\n"
                + f"[{self.mongodb_client_id_2}]\n"
                + "type = mongodb_config\n"
                + "name = Client2DB\n"
                + "read_write_connection_string = mongodb://localhost:27017\n"
                + "read_only_connection_string = mongodb://localhost:27016\n"
                + "\n"
                + f"[{self.gphotos_client_id_2}]\n"
                + "type = gphotos_config\n"
                + "name = Client2GP\n"
                + "read_write_token = t2\n"
                + "read_write_refresh_token = r2\n"
                + "read_write_client_id = id2\n"
                + "read_write_client_secret = s2\n"
                + "read_write_token_uri = https://oauth2.googleapis.com/token\n"
                + "\n"
                + f"[{ObjectId()}]\n"
                + "type = root_album\n"
                + f"client_id = {self.root_album_1.id.client_id}\n"
                + f"object_id = {self.root_album_1.id.object_id}\n"
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
                "photos_drive.cli.commands.teardown.prompt_user_for_yes_no_answer",
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

    def test_teardown_success(self):
        # 1. Seed Client 1
        sub_album = self.albums_repo_1.create_album("Sub", self.root_album_1.id)
        up = self.fake_gphotos_client_1.media_items().upload_photo("d.jpg", "d.jpg")
        res = self.fake_gphotos_client_1.media_items().add_uploaded_photos_to_gphotos(
            [up]
        )
        self.media_items_repo_1.create_media_item(
            CreateMediaItemRequest(
                file_name="d.jpg",
                file_hash=b"h",
                location=None,
                gphotos_client_id=self.gphotos_client_id_1,
                gphotos_media_item_id=res.newMediaItemResults[0].mediaItem.id,
                album_id=sub_album.id,
                width=100,
                height=100,
                date_taken=MOCK_DATE_TAKEN,
                embedding_id=None,
            )
        )

        # 2. Seed Client 2 (no root album registered in config, but global teardown hits all)
        albums_repo_2 = MongoDBAlbumsRepository(
            self.mongodb_client_id_2, self.mongodb_clients_repo
        )
        albums_repo_2.create_album("Other", None)

        runner = CliRunner()
        app = build_app()

        # Act
        result = runner.invoke(
            app, args=["teardown", "--config-file", self.config_file_path]
        )

        # Assert
        self.assertEqual(result.exit_code, 0)

        # Verify MongoDB: Only root album for client 1 remains
        self.assertEqual(
            self.mock_mongo_client_1["photos_drive"]["albums"].count_documents({}), 1
        )
        self.assertEqual(
            self.mock_mongo_client_1["photos_drive"]["media_items"].count_documents({}),
            0,
        )
        self.assertEqual(
            self.mock_mongo_client_2["photos_drive"]["albums"].count_documents({}), 0
        )

        # Verify GPhotos: "To delete" album created and item moved
        albums_1 = self.fake_gphotos_client_1.albums().list_albums()
        self.assertTrue(any(a.title == "To delete" for a in albums_1))
        trash_album = next(a for a in albums_1 if a.title == "To delete")
        media_in_trash = (
            self.fake_gphotos_client_1.media_items().search_for_media_items(
                trash_album.id
            )
        )
        self.assertEqual(len(media_in_trash), 1)

    def test_teardown_cancelled(self):
        with patch(
            "photos_drive.cli.commands.teardown.prompt_user_for_yes_no_answer",
            return_value=False,
        ):
            # Seed an album
            self.albums_repo_1.create_album("KeepMe", self.root_album_1.id)

            runner = CliRunner()
            app = build_app()

            # Act
            result = runner.invoke(
                app, args=["teardown", "--config-file", self.config_file_path]
            )

            # Assert
            self.assertEqual(result.exit_code, 0)
            # Album should still exist
            self.assertEqual(
                self.mock_mongo_client_1["photos_drive"]["albums"].count_documents(
                    {"name": "KeepMe"}
                ),
                1,
            )

    def test_teardown_reuse_trash_album(self):
        # 1. Pre-create "To delete" album
        self.fake_gphotos_client_1.albums().create_album("To delete")

        # 2. Seed an item
        up = self.fake_gphotos_client_1.media_items().upload_photo("x.jpg", "x.jpg")
        self.fake_gphotos_client_1.media_items().add_uploaded_photos_to_gphotos([up])

        runner = CliRunner()
        app = build_app()

        # Act
        result = runner.invoke(
            app, args=["teardown", "--config-file", self.config_file_path]
        )

        # Assert
        self.assertEqual(result.exit_code, 0)
        # Should still only have one "To delete" album
        albums = [
            a
            for a in self.fake_gphotos_client_1.albums().list_albums()
            if a.title == "To delete"
        ]
        self.assertEqual(len(albums), 1)
        media_in_trash = (
            self.fake_gphotos_client_1.media_items().search_for_media_items(
                albums[0].id
            )
        )
        self.assertEqual(len(media_in_trash), 1)
