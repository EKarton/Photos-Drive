import unittest
from unittest.mock import Mock, patch
import requests_mock
from freezegun import freeze_time
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from google.auth.transport import Request

from sharded_photos_drive_cli_client.shared.gphotos.client import (
    GPhotosClientV2,
    ListenableCredentials,
)
from sharded_photos_drive_cli_client.shared.gphotos.client import GPhotosStorageQuota
from sharded_photos_drive_cli_client.shared.gphotos.albums_client import (
    GPhotosAlbumsClient,
)
from sharded_photos_drive_cli_client.shared.gphotos.media_items_client import (
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
        mock_callback = Mock()
        self.listenable_credentials.set_token_refresh_callback(mock_callback)

        self.listenable_credentials.refresh(mock_request)

        mock_refresh.assert_called_once_with(mock_request)
        mock_callback.assert_called_once()

        # Check that the callback was called with a copy of the credentials
        called_credentials = mock_callback.call_args[0][0]
        self.assertIsInstance(called_credentials, Credentials)
        self.assertIsNot(called_credentials, self.listenable_credentials)

    def test_make_copy(self):
        copied_credentials = self.listenable_credentials._make_copy()
        self.assertIsInstance(copied_credentials, Credentials)
        self.assertIsNot(copied_credentials, self.listenable_credentials)

        # Check that all attributes are the same
        for attr in self.mock_credentials.keys():
            self.assertEqual(
                getattr(copied_credentials, attr),
                getattr(self.listenable_credentials, attr),
            )
