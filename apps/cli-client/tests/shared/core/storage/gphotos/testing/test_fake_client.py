import unittest

from photos_drive.shared.core.storage.gphotos.client import (
    GPhotosStorageQuota,
)
from photos_drive.shared.core.storage.gphotos.testing import (
    FakeGPhotosClient,
    FakeItemsRepository,
)


class FakeGPhotosClientTests(unittest.TestCase):
    def test_get_storage_quota__should_return_max_num_photos(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo, max_num_photos=10)

        limit = client.get_storage_quota()

        self.assertEqual(
            limit,
            GPhotosStorageQuota(
                limit=10, usage_in_drive=0, usage_in_drive_trash=0, usage=0
            ),
        )

    def test_get_storage_quota__added_three_photos(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo, max_num_photos=10)
        upload_1 = client.media_items().upload_photo('Archives/dog.png', 'dog.png')
        upload_2 = client.media_items().upload_photo('Archives/cat.png', 'cat.png')
        upload_3 = client.media_items().upload_photo('Archives/snake.png', 'snake.png')
        client.media_items().add_uploaded_photos_to_gphotos(
            [upload_1, upload_2, upload_3]
        )

        limit = client.get_storage_quota()

        self.assertEqual(
            limit,
            GPhotosStorageQuota(
                limit=10, usage_in_drive=0, usage_in_drive_trash=0, usage=3
            ),
        )

    def test_list_albums__created_albums__returns_albums(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        album_2 = client_1.albums().create_album("Photos/2012")

        albums_list = client_1.albums().list_albums()

        self.assertEqual(len(albums_list), 2)
        self.assertEqual(albums_list[0].id, album_1.id)
        self.assertEqual(albums_list[1].id, album_2.id)

    def test_list_albums__created_albums_in_different_client__returns_nothing(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_2.albums().create_album("Photos/2011")
        client_2.albums().create_album("Photos/2012")

        albums_list = client_1.albums().list_albums()

        self.assertEqual(len(albums_list), 0)

    def test_create_album__returns_album_and_response_correctly(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)

        album = client_1.albums().create_album("Photos/2011")

        albums_list = client_1.albums().list_albums()
        self.assertEqual(len(albums_list), 1)
        self.assertEqual(album.title, "Photos/2011")
        self.assertTrue(album.isWriteable)

    def test_create_album__in_different_client__returns_no_albums(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)

        client_2.albums().create_album("Photos/2011")

        albums_list = client_1.albums().list_albums()
        self.assertEqual(len(albums_list), 0)

    def test_delete_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        album_2 = client_2.albums().create_album("Photos/2012")

        client_1.albums().delete_album(album_1.id)
        client_2.albums().delete_album(album_2.id)

        albums_list_1 = client_1.albums().list_albums()
        albums_list_2 = client_2.albums().list_albums()
        self.assertEqual(len(albums_list_1), 0)
        self.assertEqual(len(albums_list_2), 0)

    def test_delete_album__in_different_client__throws_exception(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.albums().create_album("Photos/2011")
        album_2 = client_2.albums().create_album("Photos/2012")

        with self.assertRaisesRegex(ValueError, 'Cannot update album it does not own'):
            client_1.albums().delete_album(album_2.id)

    def test_add_photos_to_album__existing_album__adds_media_items_to_albums(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album = client_1.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results.newMediaItemResults[0].mediaItem.id
        client_1.albums().add_photos_to_album(album.id, [new_media_item_id])

        media_items = client_1.media_items().search_for_media_items(album.id)
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].id, new_media_item_id)

    def test_add_photos_to_album__two_albums__adds_media_items_to_both_albums(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        album_2 = client_1.albums().create_album("Photos/2012")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results.newMediaItemResults[0].mediaItem.id
        client_1.albums().add_photos_to_album(album_1.id, [new_media_item_id])
        client_1.albums().add_photos_to_album(album_2.id, [new_media_item_id])

        media_items_in_album_1 = client_1.media_items().search_for_media_items(
            album_1.id
        )
        media_items_in_album_2 = client_1.media_items().search_for_media_items(
            album_1.id
        )
        self.assertEqual(len(media_items_in_album_1), 1)
        self.assertEqual(media_items_in_album_1[0].id, new_media_item_id)
        self.assertEqual(len(media_items_in_album_2), 1)
        self.assertEqual(media_items_in_album_2[0].id, new_media_item_id)

    def test_add_photos_to_album__does_not_add_to_other_albums(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        album_2 = client_1.albums().create_album("Photos/2012")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results.newMediaItemResults[0].mediaItem.id
        client_1.albums().add_photos_to_album(album_1.id, [new_media_item_id])

        media_items_in_album_2 = client_1.media_items().search_for_media_items(
            album_2.id
        )
        self.assertEqual(len(media_items_in_album_2), 0)

    def test_add_photos_to_album__adding_photos_to_someone_elses_album__throws_error(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        album_1 = client_2.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results.newMediaItemResults[0].mediaItem.id

        with self.assertRaisesRegex(
            ValueError, "Cannot add photos to album it did not join"
        ):
            client_1.albums().add_photos_to_album(album_1.id, [new_media_item_id])

    def test_add_photos_to_album__adding_someone_elses_photos__throws_error(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        album_1 = client_2.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results.newMediaItemResults[0].mediaItem.id

        with self.assertRaisesRegex(
            ValueError, "Cannot put someone's media item into album"
        ):
            client_2.albums().add_photos_to_album(album_1.id, [new_media_item_id])

    def test_add_photos_to_album__adding_more_than_50_photos__throws_error(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        album_1 = client_2.albums().create_album("Photos/2011")
        new_media_item_ids = []
        for _ in range(100):
            upload_token = client_1.media_items().upload_photo(
                "Photos/2011/dog.jpg", "dog.jpg"
            )
            results = client_1.media_items().add_uploaded_photos_to_gphotos(
                [upload_token]
            )
            new_media_item_ids.append(results.newMediaItemResults[0].mediaItem.id)

        with self.assertRaisesRegex(
            ValueError, "Must have less than 50 media item ids"
        ):
            client_2.albums().add_photos_to_album(album_1.id, new_media_item_ids)

    def test_remove_photos_from_album__on_photo_in_album__removes_photo_from_album(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos(
            [upload_token], album_1.id
        )

        new_media_item_id = results.newMediaItemResults[0].mediaItem.id
        client_1.albums().remove_photos_from_album(album_1.id, [new_media_item_id])

        media_items_in_album_1 = client_1.media_items().search_for_media_items(
            album_1.id
        )
        self.assertEqual(len(media_items_in_album_1), 0)

    def test_remove_photos_from_album__on_someone_elses_album__throws_error(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos(
            [upload_token], album_1.id
        )
        new_media_item_id = results.newMediaItemResults[0].mediaItem.id

        with self.assertRaisesRegex(
            ValueError, "Cannot remove photos from album it did not join"
        ):
            client_2.albums().remove_photos_from_album(album_1.id, [new_media_item_id])

    def test_remove_photos_from_album__on_someone_elses_photo__throws_error(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        album_1 = client_2.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])
        new_media_item_id = results.newMediaItemResults[0].mediaItem.id

        with self.assertRaisesRegex(
            ValueError, "Cannot remove someone else's photos from album"
        ):
            client_2.albums().remove_photos_from_album(album_1.id, [new_media_item_id])

    def test_remove_photos_from_album__remove_photo_in_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos(
            [upload_token], album_1.id
        )

        new_media_item_id = results.newMediaItemResults[0].mediaItem.id
        client_1.albums().remove_photos_from_album(album_1.id, [new_media_item_id])

        media_items = client_1.media_items().search_for_media_items()
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].id, new_media_item_id)

    def test_remove_photos_from_album__remove_photo_in_two_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        album_2 = client_1.albums().create_album("Photos/2012")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos(
            [upload_token], album_1.id
        )
        new_media_item_id = results.newMediaItemResults[0].mediaItem.id
        client_1.albums().add_photos_to_album(album_2.id, [new_media_item_id])

        client_1.albums().remove_photos_from_album(album_1.id, [new_media_item_id])

        media_items = client_1.media_items().search_for_media_items(album_2.id)
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].id, new_media_item_id)

    def test_add_uploaded_photos_to_gphotos__no_album__adds_to_gphotos_account(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )

        results = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results.newMediaItemResults[0].mediaItem.id
        media_items = client_1.media_items().search_for_media_items()
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].id, new_media_item_id)

    def test_add_uploaded_photos_to_gphotos__more_than_50_items__throws_error(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        upload_tokens = [
            client_1.media_items().upload_photo(
                f"Photos/2011/dog_{i}.jpg", f"dog_{i}.jpg"
            )
            for i in range(50)
        ]

        with self.assertRaisesRegex(ValueError, "Must have less than 50 upload tokens"):
            client_1.media_items().add_uploaded_photos_to_gphotos(upload_tokens)

    def test_add_uploaded_photos_to_gphotos__regular_album__adds_to_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )

        results = client_1.media_items().add_uploaded_photos_to_gphotos(
            [upload_token], album_1.id
        )

        new_media_item_id = results.newMediaItemResults[0].mediaItem.id
        media_items = client_1.media_items().search_for_media_items(album_1.id)
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0].id, new_media_item_id)

    def test_add_uploaded_photos_to_gphotos__add_photo_to_someone_elses_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        album_1 = client_2.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )

        with self.assertRaisesRegex(
            ValueError, 'Cannot add uploaded photos to inaccessible album'
        ):
            client_1.media_items().add_uploaded_photos_to_gphotos(
                [upload_token], album_1.id
            )

    def test_upload_photo__returns_upload_token(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        upload_token = client.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )

        self.assertNotEqual(upload_token, None)

    def test_upload_photo_in_chunks__returns_upload_token(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        upload_token = client.media_items().upload_photo_in_chunks(
            "Photos/2011/dog.jpg", "dog.jpg"
        )

        self.assertNotEqual(upload_token, None)

    def test_get_all_media_items__photos_on_other_account__returns_correct_values(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])
        new_media_item_id = results.newMediaItemResults[0].mediaItem.id

        search_results_1 = client_1.media_items().get_all_media_items()
        search_results_2 = client_2.media_items().get_all_media_items()

        self.assertEqual(len(search_results_1), 1)
        self.assertEqual(search_results_1[0].id, new_media_item_id)
        self.assertEqual(len(search_results_2), 0)

    def test_search_for_media_items__no_photos__returns_nothing(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        results = client.media_items().search_for_media_items()

        self.assertEqual(len(results), 0)

    def test_search_for_media_items__photos_on_other_account__returns_correct_values(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])
        new_media_item_id = results.newMediaItemResults[0].mediaItem.id

        search_results_1 = client_1.media_items().search_for_media_items()
        search_results_2 = client_2.media_items().search_for_media_items()

        self.assertEqual(len(search_results_1), 1)
        self.assertEqual(search_results_1[0].id, new_media_item_id)
        self.assertEqual(len(search_results_2), 0)

    def test_search_for_media_items__photo_on_existing_album__returns_photos(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo(
            "Photos/2011/dog.jpg", "dog.jpg"
        )
        results = client_1.media_items().add_uploaded_photos_to_gphotos(
            [upload_token], album_1.id
        )
        new_media_item_id = results.newMediaItemResults[0].mediaItem.id

        search_results_1 = client_1.media_items().search_for_media_items(album_1.id)

        self.assertEqual(len(search_results_1), 1)
        self.assertEqual(search_results_1[0].id, new_media_item_id)

    def test_search_for_media_items__on_someone_elses_album__throws_error(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")

        with self.assertRaisesRegex(ValueError, "Cannot search in inaccessible album"):
            client_2.media_items().search_for_media_items(album_1.id)

    def test_update_album__returns_info_and_updates_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")

        updated_album_info = client_1.albums().update_album(album_1.id, "Photos/2020")

        self.assertEqual(updated_album_info.title, "Photos/2020")
        shared_albums = client_1.albums().list_albums()
        self.assertEqual(len(shared_albums), 1)
        self.assertEqual(shared_albums[0].title, "Photos/2020")

    def test_update_album__with_new_cover_media_item_id__returns_info_and_updates_album(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")
        upload_token = client_1.media_items().upload_photo("Photos/dog.png", 'dog.png')
        result = client_1.media_items().add_uploaded_photos_to_gphotos([upload_token])

        updated_album_info = client_1.albums().update_album(
            album_1.id,
            new_cover_media_item_id=result.newMediaItemResults[0].mediaItem.id,
        )

        self.assertEqual(
            updated_album_info.coverPhotoMediaItemId,
            result.newMediaItemResults[0].mediaItem.id,
        )

    def test_update_album__album_on_another_account__throws_error(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        album_1 = client_1.albums().create_album("Photos/2011")

        with self.assertRaisesRegex(ValueError, "Cannot update album it does not own"):
            client_2.albums().update_album(album_1.id, "Photos/2020")
