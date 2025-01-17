from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SharedAlbumOptions:
    """
    Represents options for a shared album.
    It has the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/albums#sharedalbumoptions.

    Attributes:
        isCollaborative (bool):
            True if the shared album allows collaborators (users who have joined the
            album) to add media items to it. Defaults to false.
        isCommentable (bool):
            True if the shared album allows collaborators (users who have joined the
            album) to add comments to the album. Defaults to false.
    """

    isCollaborative: bool
    isCommentable: bool


@dataclass(frozen=True)
class ShareInfo:
    """
    Represents information about sharing for an album in Google Photos.
    It has the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/albums#shareinfo.

    Attributes:
        sharedAlbumOptions (SharedAlbumOptions):
            Options that control whether someone can add media items to, or comment on
            a shared album.
        shareableUrl (str):
            A link to the shared Google Photos album. Anyone with the link can view the
            contents of the album, so it should be treated with care.
            The shareableUrl parameter is only returned if the album has link sharing
            turned on. If a user is already joined to an album that isn't link-shared,
            they can use the album's productUrl to access it instead.
            A shareableUrl is invalidated if the owner turns off link sharing in the
            Google Photos app, or if the album is unshared.
        shareToken (str):
            A token that is used to join, leave, or retrieve the details of a shared
            album on behalf of a user who isn't the owner.
            A shareToken is invalidated if the owner turns off link sharing in the
            Google Photos app, or if the album is unshared.
        isJoined (bool):
            True if the user is joined to the album. This is always true for the owner
            of the album.
        isOwned (bool):
            True if the user owns the album.
        isJoinable (bool):
            True if the user can join the album.
    """

    sharedAlbumOptions: SharedAlbumOptions
    shareableUrl: str
    shareToken: str
    isJoined: bool
    isOwned: bool
    isJoinable: bool


@dataclass(frozen=True)
class Album:
    """
    Represents an album to be created in Google Photos.
    It has the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/albums#resource:-album.

    Attributes:
        id (str): The ID of the album.
        title (str):
            The title of the album.
        productUrl (Optional[str]):
            Google Photos URL for the album.
        isWriteable (Optional[bool]):
            Whether the album is writeable.
        shareInfo (Optional[ShareInfo]):
            This field is only populated if the album is a shared album, the developer
            created the album and the user has granted the photoslibrary.sharing scope.
        mediaItemsCount (Optional[str]):
            Number of media items in the album.
        coverPhotoBaseUrl (Optional[str]):
            Base URL for the cover photo.
        coverPhotoMediaItemId (Optional[str]):
            ID for the media item associated with the cover photo.
    """

    id: str
    title: str
    productUrl: Optional[str] = None
    isWriteable: Optional[bool] = None
    shareInfo: Optional[ShareInfo] = None
    mediaItemsCount: Optional[str] = None
    coverPhotoBaseUrl: Optional[str] = None
    coverPhotoMediaItemId: Optional[str] = None
