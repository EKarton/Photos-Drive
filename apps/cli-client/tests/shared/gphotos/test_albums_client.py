import unittest
import requests_mock
from freezegun import freeze_time
from dacite import from_dict

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from sharded_photos_drive_cli_client.shared.gphotos.client import GPhotosClientV2
from sharded_photos_drive_cli_client.shared.gphotos.albums import Album

MOCK_CREDENTIALS = Credentials(
    token="token123",
    refresh_token="refreshToken123",
    client_id="clientId123",
    client_secret="clientSecret123",
    token_uri="tokenUri123",
)


class GPhotosAlbumClientTests(unittest.TestCase):
    def test_list_albums__multiple_pages__returns_albums_list(self):
        albums = [
            {
                "id": "1",
                "title": "Photos/2011",
                "productUrl": "https://google.com/photos/2011",
                "isWriteable": False,
                "shareInfo": None,
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
                "coverPhotoMediaItemId": "1",
            },
            {
                "id": "2",
                "title": "Photos/2012",
                "productUrl": "https://google.com/photos/2012",
                "isWriteable": False,
                "shareInfo": None,
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2012/thumbnail",
                "coverPhotoMediaItemId": "1",
            },
        ]
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=False",
                json={"albums": [albums[0]], "nextPageToken": "a"},
            )
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=False&pageToken=a",
                json={"albums": [albums[1]], "nextPageToken": "b"},
            )
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=False&pageToken=b",
                json={},
            )

            actual_albums = client.albums().list_albums()

            self.assertEqual(len(actual_albums), 2)
            self.assertEqual(actual_albums[0], from_dict(Album, albums[0]))
            self.assertEqual(actual_albums[1], from_dict(Album, albums[1]))

    def test_list_albums__multiple_pages_with_last_page_containing_no_next_page__returns_albums_list(
        self,
    ):
        albums = [
            {
                "id": "1",
                "title": "Photos/2011",
                "productUrl": "https://google.com/photos/2011",
                "isWriteable": False,
                "shareInfo": None,
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
                "coverPhotoMediaItemId": "1",
            },
            {
                "id": "2",
                "title": "Photos/2012",
                "productUrl": "https://google.com/photos/2012",
                "isWriteable": False,
                "shareInfo": None,
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2012/thumbnail",
                "coverPhotoMediaItemId": "1",
            },
        ]
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=False",
                json={"albums": [albums[0]], "nextPageToken": "a"},
            )
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=False&pageToken=a",
                json={"albums": [albums[1]]},
            )

            actual_albums = client.albums().list_albums()

            self.assertEqual(len(actual_albums), 2)
            self.assertEqual(actual_albums[0], from_dict(Album, albums[0]))
            self.assertEqual(actual_albums[1], from_dict(Album, albums[1]))

    def test_create_album__2xx__returns_album_info(self):
        mock_response = {
            "id": "1",
            "title": "Photos/2011",
            "productUrl": "https://google.com/photos/2011",
            "isWriteable": False,
            "shareInfo": None,
            "mediaItemsCount": 1,
            "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
            "coverPhotoMediaItemId": "1",
        }
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums", json=mock_response
            )

            response = client.albums().create_album("Photos/2011")

            self.assertEqual(response, from_dict(Album, mock_response))

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_create_album__first_call_returns_5xx_second_call_returns_2xx__retries_and_returns_response(
        self,
    ):
        mock_response = {
            "id": "1",
            "title": "Photos/2011",
            "productUrl": "https://google.com/photos/2011",
            "isWriteable": False,
            "shareInfo": None,
            "mediaItemsCount": 1,
            "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
            "coverPhotoMediaItemId": "1",
        }
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/albums",
                [
                    {"text": "", "status_code": 500},
                    {"json": mock_response, "status_code": 200},
                ],
            )

            response = client.albums().create_album("Photos/2011")

            self.assertEqual(response, from_dict(Album, mock_response))

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_create_album__only_5xx__throws_exception(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums",
                status_code=500,
            )

            expectedException = "500 Server Error: None for url: https://photoslibrary.googleapis.com/v1/albums"
            with self.assertRaisesRegex(Exception, expectedException):
                client.albums().create_album("Photos/2011")

    def test_add_photos_to_album__2xx__returns_nothing(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchAddMediaItems",
                json={},
            )

            response = client.albums().add_photos_to_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_add_photos_to_album__first_call_5xx_second_call_2xx__successful_and_returns_nothing(
        self,
    ):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/albums/123:batchAddMediaItems",
                [
                    {"text": "", "status_code": 500},
                    {"text": "", "status_code": 200},
                ],
            )

            response = client.albums().add_photos_to_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_add_photos_to_album__only_5xx__throws_exception(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchAddMediaItems",
                status_code=500,
            )

            expectedException = "500 Server Error: None for url: https://photoslibrary.googleapis.com/v1/albums/123:batchAddMediaItems"
            with self.assertRaisesRegex(Exception, expectedException):
                client.albums().add_photos_to_album("123", ["1", "2", "3"])

    def test_remove_photos_from_album__2xx__returns_nothing(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchRemoveMediaItems",
                json={},
            )

            response = client.albums().remove_photos_from_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_remove_photos_from_album__first_call_5xx_second_call_2xx__successful_and_returns_nothing(
        self,
    ):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/albums/123:batchRemoveMediaItems",
                [
                    {"text": "", "status_code": 500},
                    {"text": "", "status_code": 200},
                ],
            )

            response = client.albums().remove_photos_from_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_remove_photos_from_album__only_5xx__throws_exception(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchRemoveMediaItems",
                status_code=500,
            )

            expectedException = "500 Server Error: None for url: https://photoslibrary.googleapis.com/v1/albums/123:batchRemoveMediaItems"
            with self.assertRaisesRegex(Exception, expectedException):
                client.albums().remove_photos_from_album("123", ["1", "2", "3"])

    def test_update_album__with_new_title__returns_nothing(self):
        mock_response = {
            "id": "123",
            "title": "Photos/2012",
            "productUrl": "http://google.com/album/123",
            "isWriteable": True,
            "mediaItemsCount": 2,
            "coverPhotoBaseUrl": "http://google.com/media/1/thumbnail",
            "coverPhotoMediaItemId": "1",
        }

        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.patch(
                "https://photoslibrary.googleapis.com/v1/albums/123?updateMask=title",
                json=mock_response,
            )

            response = client.albums().update_album("123", new_title="Photos/2012")

            self.assertEqual(response, from_dict(Album, mock_response))

    def test_update_album__with_new_cover_media_item_id__returns_new_album_info(self):
        mock_response = {
            "id": "123",
            "title": "Photos/2011",
            "productUrl": "http://google.com/album/123",
            "isWriteable": True,
            "mediaItemsCount": 2,
            "coverPhotoBaseUrl": "http://google.com/media/2/thumbnail",
            "coverPhotoMediaItemId": "2",
        }

        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.patch(
                "https://photoslibrary.googleapis.com/v1/albums/123?updateMask=coverPhotoMediaItemId",
                json=mock_response,
            )

            response = client.albums().update_album("123", new_cover_media_item_id="2")

            self.assertEqual(response, from_dict(Album, mock_response))

    def test_update_album__with_new_title_and_new_cover_media_item_id__returns_new_album_info(
        self,
    ):
        mock_response = {
            "id": "123",
            "title": "Photos/2012",
            "productUrl": "http://google.com/album/123",
            "isWriteable": True,
            "mediaItemsCount": 2,
            "coverPhotoBaseUrl": "http://google.com/media/2/thumbnail",
            "coverPhotoMediaItemId": "2",
        }

        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.patch(
                "https://photoslibrary.googleapis.com/v1/albums/123?updateMask=title&updateMask=coverPhotoMediaItemId",
                json=mock_response,
            )

            response = client.albums().update_album(
                "123", new_title="Photos/2012", new_cover_media_item_id="2"
            )

            self.assertEqual(response, from_dict(Album, mock_response))
