import json
import tempfile
import unittest
import requests_mock
from freezegun import freeze_time
from dacite import from_dict
from google.auth.transport.requests import AuthorizedSession
from google.auth.transport import DEFAULT_RETRYABLE_STATUS_CODES
from google.oauth2.credentials import Credentials

from sharded_photos_drive_cli_client.shared.gphotos.client import GPhotosClientV2
from sharded_photos_drive_cli_client.shared.gphotos.media_items import (
    UploadedPhotosToGPhotosResult,
    MediaItem,
)

MOCK_CREDENTIALS = Credentials(
    token="token123",
    refresh_token="refreshToken123",
    client_id="clientId123",
    client_secret="clientSecret123",
    token_uri="tokenUri123",
)

MOCK_NEW_MEDIA_ITEMS_RESPONSE = {
    "newMediaItemResults": [
        {
            "status": {"message": "Success"},
            "mediaItem": {
                "id": "1",
                "description": "item-description",
                "productUrl": "https://photos.google.com/photo/photo-path",
                "mimeType": "mime-type",
                "mediaMetadata": {
                    "width": "200",
                    "height": "300",
                    "creationTime": "creation-time",
                    "photo": {},
                },
                "filename": "filename",
            },
        },
        {
            "status": {"message": "Success"},
            "mediaItem": {
                "id": "2",
                "description": "item-description",
                "productUrl": "https://photos.google.com/photo/photo-path",
                "mimeType": "mime-type",
                "mediaMetadata": {
                    "width": "200",
                    "height": "300",
                    "creationTime": "creation-time",
                    "photo": {},
                },
                "filename": "filename",
            },
        },
        {
            "status": {"message": "Success"},
            "mediaItem": {
                "id": "3",
                "description": "item-description",
                "productUrl": "https://photos.google.com/photo/photo-path",
                "mimeType": "mime-type",
                "mediaMetadata": {
                    "width": "200",
                    "height": "300",
                    "creationTime": "creation-time",
                    "photo": {},
                },
                "filename": "filename",
            },
        },
    ]
}

MOCK_GET_MEDIA_ITEMS_RESPONSE = {
    "mediaItems": [
        {
            "id": "1",
            "productUrl": "http://google.com/photos/2011/1",
            "baseUrl": "http://google.com/photos/2011/1",
            "mimeType": "jpeg",
            "filename": "dog.jpeg",
            "mediaMetadata": {
                "width": "200",
                "height": "300",
                "creationTime": "creation-time",
            },
        },
        {
            "id": "2",
            "productUrl": "http://google.com/photos/2011/2",
            "baseUrl": "http://google.com/photos/2011/2",
            "mimeType": "jpeg",
            "filename": "cat.jpeg",
            "mediaMetadata": {
                "width": "200",
                "height": "300",
                "creationTime": "creation-time",
            },
        },
    ]
}


class GPhotosMediaItemClientTests(unittest.TestCase):
    def test_add_uploaded_photos_to_gphotos__2xx__returns_new_media_items(self):

        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                json=MOCK_NEW_MEDIA_ITEMS_RESPONSE,
            )

            response = client.media_items().add_uploaded_photos_to_gphotos(
                ["u1", "u2", "u3"], "123"
            )

            self.assertEqual(
                response,
                from_dict(UploadedPhotosToGPhotosResult, MOCK_NEW_MEDIA_ITEMS_RESPONSE),
            )

    def test_add_uploaded_photos_to_gphotos__media_item_is_duplicated(self):
        mock_response = {
            "newMediaItemResults": [
                {
                    "status": {"message": "Success"},
                    "mediaItem": {
                        "id": "1",
                        "description": "item-description",
                        "productUrl": "https://photos.google.com/photo/photo-path",
                        "mimeType": "mime-type",
                        "mediaMetadata": {
                            "width": "media-width-in-px",
                            "height": "media-height-in-px",
                            "creationTime": "creation-time",
                            "photo": {},
                        },
                        "filename": "filename",
                    },
                },
                {
                    "status": {
                        "code": 6,
                        "message": "Failed to add media item: duplicate item",
                    },
                    "mediaItem": {
                        "id": "1",
                        "description": "item-description",
                        "productUrl": "https://photos.google.com/photo/photo-path",
                        "mimeType": "mime-type",
                        "mediaMetadata": {
                            "width": "media-width-in-px",
                            "height": "media-height-in-px",
                            "creationTime": "creation-time",
                            "photo": {},
                        },
                        "filename": "filename",
                    },
                },
                {
                    "status": {"message": "Success"},
                    "mediaItem": {
                        "id": "2",
                        "description": "item-description",
                        "productUrl": "https://photos.google.com/photo/photo-path",
                        "mimeType": "mime-type",
                        "mediaMetadata": {
                            "width": "media-width-in-px",
                            "height": "media-height-in-px",
                            "creationTime": "creation-time",
                            "photo": {},
                        },
                        "filename": "filename",
                    },
                },
            ]
        }

        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                json=mock_response,
            )

            response = client.media_items().add_uploaded_photos_to_gphotos(
                ["u1", "u2", "u3"], "123"
            )

            expected_response = {
                "newMediaItemResults": [
                    {
                        "status": {"message": "Success"},
                        "mediaItem": {
                            "id": "1",
                            "description": "item-description",
                            "productUrl": "https://photos.google.com/photo/photo-path",
                            "mimeType": "mime-type",
                            "mediaMetadata": {
                                "width": "media-width-in-px",
                                "height": "media-height-in-px",
                                "creationTime": "creation-time",
                                "photo": {},
                            },
                            "filename": "filename",
                        },
                    },
                    {
                        "status": {"message": "Success"},
                        "mediaItem": {
                            "id": "2",
                            "description": "item-description",
                            "productUrl": "https://photos.google.com/photo/photo-path",
                            "mimeType": "mime-type",
                            "mediaMetadata": {
                                "width": "media-width-in-px",
                                "height": "media-height-in-px",
                                "creationTime": "creation-time",
                                "photo": {},
                            },
                            "filename": "filename",
                        },
                    },
                ]
            }
            self.assertEqual(
                response, from_dict(UploadedPhotosToGPhotosResult, expected_response)
            )

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_add_uploaded_photos_to_gphotos__first_call_5xx_second_call_2xx(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                [
                    {"text": "", "status_code": 500},
                    {
                        "text": json.dumps(MOCK_NEW_MEDIA_ITEMS_RESPONSE),
                        "status_code": 200,
                    },
                ],
            )

            response = client.media_items().add_uploaded_photos_to_gphotos(
                ["u1", "u2", "u3"], "123"
            )

            self.assertEqual(
                response,
                from_dict(UploadedPhotosToGPhotosResult, MOCK_NEW_MEDIA_ITEMS_RESPONSE),
            )

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_add_uploaded_photos_to_gphotos__returns_2xx_with_retryable_codes(self):
        mock_response_1 = {
            "newMediaItemResults": [
                {
                    "status": {
                        "code": 1,
                        "message": "Cancelled",
                    },
                    "mediaItem": {
                        "id": "1",
                        "description": "item-description",
                        "productUrl": "https://photos.google.com/photo/photo-path",
                        "mimeType": "mime-type",
                        "mediaMetadata": {
                            "width": "media-width-in-px",
                            "height": "media-height-in-px",
                            "creationTime": "creation-time",
                            "photo": {},
                        },
                        "filename": "filename",
                    },
                },
            ]
        }

        mock_response_2 = {
            "newMediaItemResults": [
                {
                    "status": {"message": "Success"},
                    "mediaItem": {
                        "id": "2",
                        "description": "item-description",
                        "productUrl": "https://photos.google.com/photo/photo-path",
                        "mimeType": "mime-type",
                        "mediaMetadata": {
                            "width": "media-width-in-px",
                            "height": "media-height-in-px",
                            "creationTime": "creation-time",
                            "photo": {},
                        },
                        "filename": "filename",
                    },
                },
            ]
        }

        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                [
                    {
                        "text": json.dumps(mock_response_1),
                        "status_code": 200,
                    },
                    {
                        "text": json.dumps(mock_response_2),
                        "status_code": 200,
                    },
                ],
            )

            response = client.media_items().add_uploaded_photos_to_gphotos(
                ["u1"], "123"
            )

            self.assertEqual(
                response,
                from_dict(UploadedPhotosToGPhotosResult, mock_response_2),
            )

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_add_uploaded_photos_to_gphotos__returns_2xx_with_unknown_codes(self):
        mock_response = {
            "newMediaItemResults": [
                {
                    "status": {
                        "code": 101010,
                        "message": "Hehe",
                    },
                    "mediaItem": {
                        "id": "1",
                        "description": "item-description",
                        "productUrl": "https://photos.google.com/photo/photo-path",
                        "mimeType": "mime-type",
                        "mediaMetadata": {
                            "width": "media-width-in-px",
                            "height": "media-height-in-px",
                            "creationTime": "creation-time",
                            "photo": {},
                        },
                        "filename": "filename",
                    },
                },
            ]
        }

        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                [
                    {
                        "text": json.dumps(mock_response),
                        "status_code": 200,
                    },
                ],
            )

            with self.assertRaisesRegex(ValueError, "code: 101010, message: Hehe"):
                client.media_items().add_uploaded_photos_to_gphotos(["u1"], "123")

    def test_upload_photo__2xx__returns_upload_token(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/uploads",
                text="u1",
            )

            with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as mock_file:
                response = client.media_items().upload_photo(mock_file.name, "dog.jpg")

                self.assertEqual(response, "u1")

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_upload_photo__first_call_5xx_second_call_2xx(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/uploads",
                [
                    {"text": "", "status_code": 500},
                    {"text": "u1", "status_code": 200},
                ],
            )

            with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as mock_file:
                response = client.media_items().upload_photo(mock_file.name, "dog.jpg")

                self.assertEqual(response, "u1")

    def test_search_for_media_items__2xx__returns_media_items(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                json=MOCK_GET_MEDIA_ITEMS_RESPONSE,
            )

            response = client.media_items().search_for_media_items(album_id="123")

            self.assertEqual(
                response[0],
                from_dict(MediaItem, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"][0]),
            )
            self.assertEqual(
                response[1],
                from_dict(MediaItem, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"][1]),
            )

    def test_search_for_media_items__response_in_two_pages__returns_media_items(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                json={
                    "mediaItems": [MOCK_GET_MEDIA_ITEMS_RESPONSE['mediaItems'][0]],
                    "nextPageToken": "a",
                },
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                json={
                    "mediaItems": [MOCK_GET_MEDIA_ITEMS_RESPONSE['mediaItems'][1]],
                },
                additional_matcher=lambda request: request.json()['pageToken'] == 'a',
            )

            response = client.media_items().search_for_media_items(album_id="123")

            self.assertEqual(
                response[0],
                from_dict(MediaItem, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"][0]),
            )
            self.assertEqual(
                response[1],
                from_dict(MediaItem, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"][1]),
            )

    def test_search_for_media_items__second_page_no_mediaItems_field(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                json={
                    "mediaItems": MOCK_GET_MEDIA_ITEMS_RESPONSE['mediaItems'],
                    "nextPageToken": "a",
                },
            )
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                json={},
                additional_matcher=lambda request: request.json()['pageToken'] == 'a',
            )

            response = client.media_items().search_for_media_items(album_id="123")

            self.assertEqual(
                response[0],
                from_dict(MediaItem, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"][0]),
            )
            self.assertEqual(
                response[1],
                from_dict(MediaItem, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"][1]),
            )

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_search_for_media_items__first_call_5xx_second_call_2xx(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                [
                    {"text": "", "status_code": 500},
                    {
                        "text": json.dumps(MOCK_GET_MEDIA_ITEMS_RESPONSE),
                        "status_code": 200,
                    },
                ],
            )

            response = client.media_items().search_for_media_items(album_id="123")

            self.assertEqual(
                response[0],
                from_dict(MediaItem, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"][0]),
            )
            self.assertEqual(
                response[1],
                from_dict(MediaItem, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"][1]),
            )

    def test_upload_photo_in_chunks__large_file(self):
        get_upload_link_url = "https://photoslibrary.googleapis.com/v1/uploads"
        upload_url = "https://photoslibrary.googleapis.com/v1/upload-url/1"
        with requests_mock.Mocker() as request_mocker:
            request_mocker.post(
                get_upload_link_url,
                status_code=200,
                headers={
                    "X-Goog-Upload-URL": upload_url,
                    "X-Goog-Upload-Chunk-Granularity": "234567",
                },
                text="",
            )
            request_mocker.post(upload_url, status_code=200, text="1234-upload-token")

            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            upload_token = client.media_items().upload_photo_in_chunks(
                photo_file_path="./tests/shared/gphotos/resources/small-image.jpg",
                file_name="small-image.jpg",
            )

            self.assertEqual(upload_token, "1234-upload-token")
            self.assertEqual(len(request_mocker.request_history), 13)
            req_1 = request_mocker.request_history[0]
            self.assertEqual(req_1.url, get_upload_link_url)
            self.assertEqual(req_1.headers["Content-Length"], "0")
            self.assertEqual(req_1.headers["X-Goog-Upload-Command"], "start")
            self.assertEqual(req_1.headers["X-Goog-Upload-Content-Type"], "image/jpeg")
            self.assertEqual(req_1.headers["X-Goog-Upload-Protocol"], "resumable")
            self.assertEqual(req_1.headers["X-Goog-Upload-Raw-Size"], "2622777")

            for i in range(1, 12):
                req_i = request_mocker.request_history[i]
                self.assertEqual(req_i.url, upload_url)
                self.assertEqual(req_i.headers["X-Goog-Upload-Command"], "upload")
                self.assertEqual(
                    req_i.headers["X-Goog-Upload-Offset"], str((i - 1) * 234567)
                )

            req_13 = request_mocker.request_history[12]
            self.assertEqual(req_13.url, upload_url)
            self.assertEqual(
                req_13.headers["X-Goog-Upload-Command"], "upload, finalize"
            )
            self.assertEqual(req_13.headers["X-Goog-Upload-Offset"], "2580237")

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=10000)
    def test_upload_photo_in_chunks__uploading_middle_chunk_failed(self):
        get_upload_link_url = "https://photoslibrary.googleapis.com/v1/uploads"
        upload_url = "https://photoslibrary.googleapis.com/v1/upload-url/1"
        upload_token = "1234-upload-token"
        with requests_mock.Mocker() as request_mocker:
            request_mocker.register_uri(
                "POST",
                get_upload_link_url,
                status_code=200,
                headers={
                    "X-Goog-Upload-URL": upload_url,
                    "X-Goog-Upload-Chunk-Granularity": "234567",
                },
                text="",
            )

            first_time_called = False

            def post_upload_url_callback(request, context):
                nonlocal first_time_called

                if request.headers["X-Goog-Upload-Command"] == "query":
                    context.headers["X-Goog-Upload-Size-Received"] = "0"
                    context.headers["X-Goog-Upload-Status"] = "active"
                    context.status_code = 200
                else:
                    if not first_time_called:
                        context.status_code = 400
                        first_time_called = True
                    else:
                        context.status_code = 200
                        return upload_token

            request_mocker.register_uri(
                "POST", upload_url, text=post_upload_url_callback
            )

            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            received_upload_token = client.media_items().upload_photo_in_chunks(
                photo_file_path="./tests/shared/gphotos/resources/small-image.jpg",
                file_name="small-image.jpg",
            )

            self.assertEqual(received_upload_token, upload_token)
            self.assertEqual(len(request_mocker.request_history), 15)

            # First request is to start the chunking upload
            req_1 = request_mocker.request_history[0]
            self.assertEqual(req_1.url, get_upload_link_url)
            self.assertEqual(req_1.headers["Content-Length"], "0")
            self.assertEqual(req_1.headers["X-Goog-Upload-Command"], "start")
            self.assertEqual(req_1.headers["X-Goog-Upload-Content-Type"], "image/jpeg")
            self.assertEqual(req_1.headers["X-Goog-Upload-Protocol"], "resumable")
            self.assertEqual(req_1.headers["X-Goog-Upload-Raw-Size"], "2622777")

            # Second request is to try to upload the first chunk
            req_2 = request_mocker.request_history[1]
            self.assertEqual(req_2.url, upload_url)
            self.assertEqual(req_2.headers["X-Goog-Upload-Command"], "upload")
            self.assertEqual(req_2.headers["X-Goog-Upload-Offset"], "0")

            # Third request is to query the issue
            req_3 = request_mocker.request_history[2]
            self.assertEqual(req_3.url, upload_url)
            self.assertEqual(req_3.headers["X-Goog-Upload-Command"], "query")
            self.assertEqual(req_3.headers["Content-Length"], "0")

            # Requests 3, 4, ..., 15 is to upload the chunks
            for i in range(3, 14):
                req_i = request_mocker.request_history[i]
                self.assertEqual(req_i.url, upload_url)
                self.assertEqual(req_i.headers["X-Goog-Upload-Command"], "upload")
                self.assertEqual(
                    req_i.headers["X-Goog-Upload-Offset"], str((i - 3) * 234567)
                )

            # Last request is to upload the last chunk
            req_15 = request_mocker.request_history[14]
            self.assertEqual(req_15.url, upload_url)
            self.assertEqual(
                req_15.headers["X-Goog-Upload-Command"], "upload, finalize"
            )
            self.assertEqual(req_15.headers["X-Goog-Upload-Offset"], "2580237")

    def test_upload_photo_in_chunks__uploading_middle_chunk_failed_query_failed(self):
        get_upload_link_url = "https://photoslibrary.googleapis.com/v1/uploads"
        upload_url = "https://photoslibrary.googleapis.com/v1/upload-url/1"
        upload_token = "1234-upload-token"
        with requests_mock.Mocker() as request_mocker:
            request_mocker.register_uri(
                "POST",
                get_upload_link_url,
                status_code=200,
                headers={
                    "X-Goog-Upload-URL": upload_url,
                    "X-Goog-Upload-Chunk-Granularity": "234567",
                },
                text="",
            )

            first_time_called = False

            def post_upload_url_callback(request, context):
                nonlocal first_time_called

                if request.headers["X-Goog-Upload-Command"] == "query":
                    context.headers["X-Goog-Upload-Size-Received"] = "0"
                    context.headers["X-Goog-Upload-Status"] = "invalid"
                    context.status_code = 200
                else:
                    if not first_time_called:
                        context.status_code = 400
                        first_time_called = True
                    else:
                        context.status_code = 200
                        return upload_token

            request_mocker.register_uri(
                "POST", upload_url, text=post_upload_url_callback
            )

            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )

            received_upload_token = client.media_items().upload_photo_in_chunks(
                photo_file_path="./tests/shared/gphotos/resources/small-image.jpg",
                file_name="small-image.jpg",
            )

            self.assertEqual(received_upload_token, upload_token)

    def test_upload_photo_in_chunks__uploading_middle_chunk_failed_with_retryable_code(
        self,
    ):
        get_upload_link_url = "https://photoslibrary.googleapis.com/v1/uploads"
        upload_url = "https://photoslibrary.googleapis.com/v1/upload-url/1"
        upload_token = "1234-upload-token"
        with requests_mock.Mocker() as request_mocker:
            request_mocker.register_uri(
                "POST",
                get_upload_link_url,
                status_code=200,
                headers={
                    "X-Goog-Upload-URL": upload_url,
                    "X-Goog-Upload-Chunk-Granularity": "234567",
                },
                text="",
            )

            first_time_called = False

            def post_upload_url_callback(request, context):
                nonlocal first_time_called

                if not first_time_called:
                    context.status_code = DEFAULT_RETRYABLE_STATUS_CODES[0]
                    first_time_called = True
                else:
                    context.status_code = 200
                    return upload_token

            request_mocker.register_uri(
                "POST", upload_url, text=post_upload_url_callback
            )

            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )

            received_upload_token = client.media_items().upload_photo_in_chunks(
                photo_file_path="./tests/shared/gphotos/resources/small-image.jpg",
                file_name="small-image.jpg",
            )

            self.assertEqual(received_upload_token, upload_token)

    def test_upload_photo_in_chunks__missing_upload_token_in_last_chunk__throws_error(
        self,
    ):
        get_upload_link_url = "https://photoslibrary.googleapis.com/v1/uploads"
        upload_url = "https://photoslibrary.googleapis.com/v1/upload-url/1"
        with requests_mock.Mocker() as request_mocker:
            request_mocker.post(
                get_upload_link_url,
                status_code=200,
                headers={
                    "X-Goog-Upload-URL": upload_url,
                    "X-Goog-Upload-Chunk-Granularity": "234567",
                },
                text="",
            )
            request_mocker.post(upload_url, status_code=200)

            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )

            with self.assertRaisesRegex(ValueError, "Failed to get upload token"):
                client.media_items().upload_photo_in_chunks(
                    photo_file_path="./tests/shared/gphotos/resources/small-image.jpg",
                    file_name="small-image.jpg",
                )
