from dataclasses import dataclass
from typing import Callable, Optional
from google.oauth2.credentials import Credentials
from requests.exceptions import RequestException
from google.auth.transport.requests import AuthorizedSession
import backoff

from .albums_client import GPhotosAlbumsClient
from .media_items_client import GPhotosMediaItemsClient


@dataclass(frozen=True)
class GPhotosStorageQuota:
    """
    Represents the amount of space in the Google Photos account.

    Attributes:
        limit (int):
            The usage limit, if applicable. This will not be present if the user has
            unlimited storage. For users that are part of an organization with pooled
            storage, this is the limit for the organization, rather than the
            individual user.

        usage_in_drive (int):
            The usage by all files in Google Drive.

        usage_in_drive_trash (int):
            The usage by trashed files in Google Drive.

        usage (int):
            The total usage across all services. For users that are part of an
            organization with pooled storage, this is the usage across all services for
            the organization, rather than the individual user.
    """

    limit: int
    usage_in_drive: int
    usage_in_drive_trash: int
    usage: int


class GPhotosClientV2:
    """
    Represents a client for a Google Photos account.
    """

    def __init__(self, name: str, session: AuthorizedSession):
        """
        Initializes the GPhotosClientV2 object

        Args:
            name (str): The name of the Google Photos client.
            session (AuthorizedSession): The current session.
        """
        self._name = name
        self._session = session
        self._albums_client = GPhotosAlbumsClient(session)
        self._media_items_client = GPhotosMediaItemsClient(session)

    @backoff.on_exception(backoff.expo, (RequestException), max_time=60)
    def get_storage_quota(self) -> GPhotosStorageQuota:
        """
        Returns the storage quota for the Google account.

        Returns:
            GPhotosStorageQuota: The storage quota.
        """
        params = {"fields": "storageQuota"}
        uri = "https://www.googleapis.com/drive/v3/about"
        res = self._session.get(uri, params=params)
        res.raise_for_status()

        raw_obj = res.json()["storageQuota"]
        return GPhotosStorageQuota(
            limit=int(raw_obj["limit"]),
            usage_in_drive=int(raw_obj["usageInDrive"]),
            usage_in_drive_trash=int(raw_obj["usageInDriveTrash"]),
            usage=int(raw_obj["usage"]),
        )

    def name(self) -> str:
        """Returns the name of the Google Photos account."""
        return self._name

    def session(self) -> AuthorizedSession:
        """Returns the session of the Google Photos account."""
        return self._session

    def albums(self) -> GPhotosAlbumsClient:
        """Returns the albums client of the Google Photos account."""
        return self._albums_client

    def media_items(self) -> GPhotosMediaItemsClient:
        """Returns the media items client of the Google Photos account."""
        return self._media_items_client


class ListenableCredentials(Credentials):
    '''
    A type of Credential where every time the token refreshes,
    it calls the callback function.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token_refresh_callback = None

    def refresh(self, request):
        super().refresh(request)
        if self.token_refresh_callback:
            self.token_refresh_callback(self)

    def set_token_refresh_callback(
        self, callback: Optional[Callable[[Credentials], None]]
    ):
        '''
        Sets the token refresh callback.

        Args:
            callback (Optional[Callable[[Credentials], None]]):
                The callback function, which returns the new credentials whenever the
                token is refreshed.
        '''
        self.token_refresh_callback = callback
