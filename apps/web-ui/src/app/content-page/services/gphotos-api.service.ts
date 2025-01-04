import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

/**
 * Represents the details of a Google Photos media item.
 * It should be the same as in https://developers.google.com/photos/library/reference/rest/v1/mediaItems#resource:-mediaitem.
 */
export interface GPhotosMediaItemDetails {
  /** Identifier for the media item. This is a persistent identifier that can be used between sessions to identify this media item. */
  id: string;

  /** Description of the media item. This is shown to the user in the item's info section in the Google Photos app. Must be shorter than 1000 characters. Only include text written by users. Descriptions should add context and help users understand media. Do not include any auto-generated strings such as filenames, tags, and other metadata.   */
  description: string;

  /** Google Photos URL for the media item. This link is available to the user only if they're signed in. When retrieved from an album search, the URL points to the item inside the album. */
  productUrl: string;

  /** A URL to the media item's bytes. This shouldn't be used as is. Parameters should be appended to this URL before use. See the developer documentation for a complete list of supported parameters. For example, '=w2048-h1024' will set the dimensions of a media item of type photo to have a width of 2048 px and height of 1024 px. */
  baseUrl: string;

  /** MIME type of the media item. For example, image/jpeg. */
  mimeType: string;

  /** Metadata related to the media item, such as, height, width, or creation time. */
  mediaMetadata: {
    creationTime: string;
    width: number;
    height: number;
  };

  /** Information about the user who added this media item. Note that this is only included when using mediaItems.search with the ID of a shared album. The album must be created by your app and you must have the sharing scope. */
  contributorInfo: {
    profilePictureBaseUrl: string;
    displayName: string;
  };

  /** Filename of the media item. This is shown to the user in the item's info section in the Google Photos app. */
  filename: string;
}

export type GPhotosMediaItemApiResponse = GPhotosMediaItemDetails;

@Injectable({ providedIn: 'root' })
export class GhotosApiService {
  private readonly httpClient = inject(HttpClient);

  /**
   * Fetches the details of a media item stored on Google Photos.
   *
   * @param token The access token.
   * @param mediaItemId The media item ID in Google Photos.
   * @return An observable with the results in there.
   */
  fetchMediaItemDetail(
    token: string,
    mediaItemId: string,
  ): Observable<GPhotosMediaItemApiResponse> {
    const url = `https://photoslibrary.googleapis.com/v1/mediaItems/${mediaItemId}`;
    return this.httpClient.get<GPhotosMediaItemApiResponse>(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }
}
