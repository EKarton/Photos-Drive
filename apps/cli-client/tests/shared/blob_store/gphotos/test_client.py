import unittest
from unittest.mock import Mock, patch
import requests_mock
from freezegun import freeze_time
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from google.auth.transport import Request

from photos_drive.shared.blob_store.gphotos.client import (
    GPhotosClientV2,
    ListenableCredentials,
    TokenRefreshCallback,
)
from photos_drive.shared.blob_store.gphotos.client import (
    GPhotosStorageQuota,
)
from photos_drive.shared.blob_store.gphotos.albums_client import (
    GPhotosAlbumsClient,
)
from photos_drive.shared.blob_store.gphotos.media_items_client import (
    GPhotosMediaItemsClient,
)

MOCK_CREDENTIALS = Credentials(
    token="token123",
    refresh_token="refreshToken123",
    client_id="clientId123",
    client_secret="clientSecret123",
    token_uri="tokenUri123",
)

MOCK_GET_STORAGE_QUOTA_RESPONSE = {
    "storageQuota": {
        "limit": "1234",
        "usage": "123",
        "usageInDrive": "0",
        "usageInDriveTrash": "0",
    }
}

MOCK_GPHOTOS_STORAGE_QUOTA = GPhotosStorageQuota(
    limit=1234, usage=123, usage_in_drive=0, usage_in_drive_trash=0
)


class GPhotosClientTests(unittest.TestCase):
    def test_get_storage_quota__returns_storage_quota(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.get(
                "https://www.googleapis.com/drive/v3/about",
                json=MOCK_GET_STORAGE_QUOTA_RESPONSE,
            )

            storage_quota = client.get_storage_quota()

            self.assertEqual(storage_quota, MOCK_GPHOTOS_STORAGE_QUOTA)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_get_storage_quota__first_call_5xx_second_call_2xx(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.register_uri(
                "GET",
                "https://www.googleapis.com/drive/v3/about",
                [
                    {"text": "", "status_code": 500},
                    {"json": MOCK_GET_STORAGE_QUOTA_RESPONSE, "status_code": 200},
                ],
            )

            storage_quota = client.get_storage_quota()

            self.assertEqual(storage_quota, MOCK_GPHOTOS_STORAGE_QUOTA)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_get_storage_quota__only_5xx__throws_exception(self):
        with requests_mock.Mocker() as request_mocker:
            client = GPhotosClientV2(
                "bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS)
            )
            request_mocker.get(
                "https://www.googleapis.com/drive/v3/about",
                status_code=500,
            )

            expectedException = (
                "500 Server Error: None for url: "
                + "https://www.googleapis.com/drive/v3/about"
            )
            with self.assertRaisesRegex(Exception, expectedException):
                client.get_storage_quota()

    def test_name__returns_name(self):
        client = GPhotosClientV2("bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS))

        self.assertEqual(client.name(), "bob@gmail.com")

    def test_session__returns_session(self):
        session = AuthorizedSession(MOCK_CREDENTIALS)
        client = GPhotosClientV2("bob@gmail.com", session)

        self.assertEqual(client.session(), session)

    def test_albums__returns_instance_of_albums_client(self):
        client = GPhotosClientV2("bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS))

        self.assertIsInstance(client.albums(), GPhotosAlbumsClient)

    def test_media_items__returns_instance_of_media_items_client(self):
        client = GPhotosClientV2("bob@gmail.com", AuthorizedSession(MOCK_CREDENTIALS))

        self.assertIsInstance(client.media_items(), GPhotosMediaItemsClient)


class TestListenableCredentials(unittest.TestCase):

    def setUp(self):
        self.mock_credentials = {
            'token': 'fake_token',
            'refresh_token': 'fake_refresh_token',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': 'fake_client_id',
            'client_secret': 'fake_client_secret',
            'scopes': ['https://www.googleapis.com/auth/photoslibrary.readonly'],
        }
        self.listenable_credentials = ListenableCredentials(**self.mock_credentials)

    def test_initialization(self):
        self.assertIsInstance(self.listenable_credentials, Credentials)

    @patch.object(Credentials, 'refresh')
    def test_refresh_without_callback(self, mock_refresh):
        mock_request = Mock(spec=Request)
        self.listenable_credentials.refresh(mock_request)

        mock_refresh.assert_called_once_with(mock_request)

    @patch.object(Credentials, 'refresh')
    def test_refresh_with_callback(self, mock_refresh):
        mock_request = Mock(spec=Request)
        mock_callback = Mock(spec=TokenRefreshCallback)
        self.listenable_credentials.set_token_refresh_callback(mock_callback)

        self.listenable_credentials.refresh(mock_request)

        mock_callback.before_refresh.assert_called_once()
        mock_refresh.assert_called_once_with(mock_request)
        mock_callback.after_refresh.assert_called_once()

    @patch.object(Credentials, 'refresh')
    def test_refresh_with_failed_before_callback(self, mock_refresh):
        mock_request = Mock(spec=Request)
        mock_callback = Mock(spec=TokenRefreshCallback)
        test_error = Exception("Random error")
        mock_callback.before_refresh.side_effect = test_error
        self.listenable_credentials.set_token_refresh_callback(mock_callback)

        self.listenable_credentials.refresh(mock_request)

        mock_callback.before_refresh.assert_called_once()
        mock_refresh.assert_not_called()
        mock_callback.after_refresh.assert_called_once_with(test_error)

    @patch.object(Credentials, 'refresh')
    def test_refresh_with_failed_refresh(self, mock_refresh):
        mock_request = Mock(spec=Request)
        mock_callback = Mock(spec=TokenRefreshCallback)
        test_error = Exception("Random error")
        mock_refresh.side_effect = test_error
        self.listenable_credentials.set_token_refresh_callback(mock_callback)

        self.listenable_credentials.refresh(mock_request)

        mock_callback.before_refresh.assert_called_once()
        mock_refresh.assert_called_once()
        mock_callback.after_refresh.assert_called_once_with(test_error)
