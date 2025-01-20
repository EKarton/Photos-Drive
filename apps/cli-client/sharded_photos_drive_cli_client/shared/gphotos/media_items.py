from dataclasses import dataclass
from typing import Optional
from enum import Enum


@dataclass(frozen=True)
class Status:
    """
    Represents the status of an HTTP request.
    It follows the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/Status.

    Attributes:
        message (str):
            A developer-facing error message, which should be in English.
            Any user-facing error message should be localized and sent in the
            google.rpc.Status.details field, or localized by the client.
        details (list[tuple[str, str]]):
            A list of messages that carry the error details. There is a common set of
            message types for APIs to use.
            An object containing fields of an arbitrary type.
            An additional field "@type" contains a URI identifying the type.
            Example: { "id": 1234, "@type": "types.example.com/standard/id" }.
        code (int):
            The status code, which should be an enum value of google.rpc.Code.
    """

    message: str
    details: Optional[list[tuple[str, str]]] = None
    code: Optional[int] = None


@dataclass(frozen=True)
class PhotoMetadata:
    """
    Represents photo metadata for a media item.
    It follows the same data model as:
    https://developers.google.com/photos/library/reference/rest/v1/mediaItems#photo.

    Attributes:
        cameraMake (Optional[str]):
            Brand of the camera with which the photo was taken.
        cameraModel (Optional[str]):
            Model of the camera with which the photo was taken.
        focalLength (Optional[float]):
            Focal length of the camera lens with which the photo was taken.
        apertureFNumber (Optional[float]):
            Aperture f number of the camera lens with which the photo was taken.
        isoEquivalent (Optional[int]):
            ISO of the camera with which the photo was taken.
        exposureTime (Optional[str]):
            Exposure time of the camera aperture when the photo was taken.
            A duration in seconds with up to nine fractional digits, ending with 's'.
            Example: "3.5s".
    """

    cameraMake: Optional[str] = None
    cameraModel: Optional[str] = None
    focalLength: Optional[float] = None
    apertureFNumber: Optional[float] = None
    isoEquivalent: Optional[int] = None
    exposureTime: Optional[str] = None


class VideoProcessingStatus(Enum):
    """
    Processing status of a video being uploaded to Google Photos.
    It follows the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/mediaItems#videoprocessingstatus.
    """

    # Video processing status is unknown.
    UNSPECIFIED = "UNSPECIFIED"

    # Video is being processed. The user sees an icon for this video in the Google
    # Photos app; however, it isn't playable yet.
    PROCESSING = "PROCESSING"

    # Video processing is complete and it is now ready for viewing.
    # Important: attempting to download a video not in the READY state may fail.
    READY = "READY"

    # Something has gone wrong and the video has failed to process.
    FAILED = "FAILED"


@dataclass(frozen=True)
class VideoMetadata:
    """
    Metadata specific to a video.
    It follows the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/mediaItems#Photo.

    Attributes:
        cameraMake (Optional[str]):
            Brand of the camera with which the video was taken.
        cameraModel (Optional[str]):
            Model of the camera with which the video was taken.
        fps (Optional[float]):
            Frame rate of the video.
        status (Optional[VideoProcessingStatus]):
            Processing status of the video.
    """

    cameraMake: Optional[str] = None
    cameraModel: Optional[str] = None
    fps: Optional[float] = None
    status: Optional[VideoProcessingStatus] = None


@dataclass(frozen=True)
class MediaMetadata:
    """
    Represents the metadata of a media item.
    It follows the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/mediaItems#mediametadata.

    Attributes:
        creationTime (Optional[str]):
            Time when the media item was first created (not when it was uploaded to
            Google Photos).
            A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up
            to nine fractional digits.
            Examples: "2014-10-02T15:01:23Z" and "2014-10-02T15:01:23.045123456Z".
            It is null when the video is still processing.
        width (Optional[str]):
            Original width (in pixels) of the media item.
            If the video is still processing, the width can be unavailable and will be
            null.
        height (Optional[str]):
            Original height (in pixels) of the media item.
            If the video is still processing, the height can be unavailable and will be
            null.
        photo (Optional[PhotoMetadata]):
            If it's a photo, it will have photo-specific metadata
        video (Optional[VideoMetadata]):
            If it's a video, it will have video-specific metadata

    """

    creationTime: Optional[str]
    width: Optional[str]
    height: Optional[str]
    photo: Optional[PhotoMetadata]
    video: Optional[VideoMetadata]


@dataclass(frozen=True)
class ContributorInfo:
    """
    Information about the user who added the media item.

    Attributes:
        profilePictureBaseUrl (str):
            URL to the profile picture of the contributor.
        displayName (str):
            Display name of the contributor.
    """

    profilePictureBaseUrl: str
    displayName: str


@dataclass(frozen=True)
class MediaItem:
    """
    Represents a media item in Google Photos.
    It follows the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/mediaItems#MediaItem.

    Attributes:
        id (str):
            Identifier for the media item.
        description (Optional[str]):
            Description of the media item.
        productUrl (str):
            Google Photos URL for the media item.
        baseUrl (str):
            A URL to the media item's bytes.
        mimeType (str):
            MIME type of the media item.
        mediaMetadata (MediaMetadata):
            Metadata related to the media item.
        contributorInfo (Optional[ContributorInfo]):
            Information about the user who added this media item.
        filename (str):
            Filename of the media item.


    """

    id: str
    description: Optional[str]
    productUrl: str
    baseUrl: Optional[str]
    mimeType: str
    mediaMetadata: MediaMetadata
    contributorInfo: Optional[ContributorInfo]
    filename: str


@dataclass(frozen=True)
class NewMediaItemResult:
    """
    Represents the results from adding a new media item to Google Photos.
    It follows the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/mediaItems/batchCreate#newmediaitemresult.

    Attributes:
        uploadToken (str):
            The upload token used to create this new (simple) media item.
            Only populated if the media item is simple and required a single upload
            token.
        status (Status):
            If an error occurred during the creation of this media item, this field is
            populated with information related to the error.
        mediaItem (MediaItem):
            Media item created with the upload token. It's populated if no errors
            occurred and the media item was created successfully.

    """

    uploadToken: Optional[str]
    mediaItem: MediaItem
    status: Status


@dataclass(frozen=True)
class UploadedPhotosToGPhotosResult:
    """
    Represents the results from the bulk additon of media items to Google Photos.
    It follows the same data model as in:
    https://developers.google.com/photos/library/reference/rest/v1/mediaItems/batchCreate.

    Attributes:
        newMediaItemResults (list[NewMediaItemResult]):
            A list of media items created.

    """

    newMediaItemResults: list[NewMediaItemResult]
