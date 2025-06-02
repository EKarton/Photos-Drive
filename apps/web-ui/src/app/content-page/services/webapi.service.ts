import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Result } from '../../shared/results/results';
import { toResult } from '../../shared/results/rxjs/toResult';

/** Represents an album. */
export interface Album {
  id: string;
  albumName: string;
  parentAlbumId?: string;
  childAlbumIds: string[];
  mediaItemIds: string[];
}

/** Represents the api response returned from {@code getAlbum()} */
export type AlbumDetailsApiResponse = Album;

export interface MediaItemLocation {
  latitude: number;
  longitude: number;
}

export interface MediaItem {
  id: string;
  fileName: string;
  hashCode: string;
  location?: MediaItemLocation;
  gPhotosMediaItemId: string;
}

export type MediaItemDetailsApiResponse = MediaItem;

export enum ListMediaItemsInAlbumSortByFields {
  ID = 'id',
}

export enum ListMediaItemsInAlbumSortDirection {
  ASCENDING = 'asc',
  DESCENDING = 'desc',
}

export interface ListMediaItemsInAlbumSortBy {
  field: ListMediaItemsInAlbumSortByFields;
  direction: ListMediaItemsInAlbumSortDirection;
}

export interface ListMediaItemsInAlbumRequest {
  albumId: string;
  pageSize?: number;
  pageToken?: string;
  sortBy?: ListMediaItemsInAlbumSortBy;
}

export interface ListMediaItemsInAlbumResponse {
  mediaItems: MediaItem[];
  nextPageToken?: string;
}

/**
 * Represents the status of an HTTP request.
 * Follows the data model at:
 * https://developers.google.com/photos/library/reference/rest/v1/Status.
 */
export interface Status {
  /** A developer-facing error message in English. */
  message: string;
  /** A list of messages that carry error details. Each tuple contains two strings. */
  details?: [string, string][];
  /** The status code, corresponding to an enum value of google.rpc.Code. */
  code?: number;
}

/**
 * Represents photo metadata for a media item.
 * Follows the data model at:
 * https://developers.google.com/photos/library/reference/rest/v1/mediaItems#photo.
 */
export interface GPhotosPhotoMetadata {
  /** Brand of the camera with which the photo was taken. */
  cameraMake?: string;
  /** Model of the camera with which the photo was taken. */
  cameraModel?: string;
  /** Focal length of the camera lens used. */
  focalLength?: number;
  /** Aperture f number of the camera lens used. */
  apertureFNumber?: number;
  /** ISO equivalent value of the camera. */
  isoEquivalent?: number;
  /** Exposure time of the camera aperture when the photo was taken (e.g., "3.5s"). */
  exposureTime?: string;
}

/**
 * Processing status of a video being uploaded to Google Photos.
 * Follows the data model at:
 * https://developers.google.com/photos/library/reference/rest/v1/mediaItems#videoprocessingstatus.
 */
export enum GPhotosVideoProcessingStatus {
  UNSPECIFIED = 'UNSPECIFIED',
  PROCESSING = 'PROCESSING',
  READY = 'READY',
  FAILED = 'FAILED',
}

/**
 * Metadata specific to a video.
 * Follows the data model at:
 * https://developers.google.com/photos/library/reference/rest/v1/mediaItems#video.
 */
export interface GPhotosVideoMetadata {
  /** Brand of the camera with which the video was taken. */
  cameraMake?: string;
  /** Model of the camera with which the video was taken. */
  cameraModel?: string;
  /** Frame rate of the video. */
  fps?: number;
  /** Processing status of the video. */
  status?: GPhotosVideoProcessingStatus;
}

/**
 * Represents the metadata of a media item.
 * Follows the data model at:
 * https://developers.google.com/photos/library/reference/rest/v1/mediaItems#mediametadata.
 */
export interface GPhotosMediaMetadata {
  /**
   * Time when the media item was first created (not when it was uploaded to Google Photos).
   * A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution.
   */
  creationTime?: string;
  /** Original width (in pixels) of the media item. May be null if unavailable. */
  width?: string;
  /** Original height (in pixels) of the media item. May be null if unavailable. */
  height?: string;
  /** Photo-specific metadata, if applicable. */
  photo?: GPhotosPhotoMetadata;
  /** Video-specific metadata, if applicable. */
  video?: GPhotosVideoMetadata;
}

/**
 * Represents a media item in Google Photos.
 * Follows the data model at:
 * https://developers.google.com/photos/library/reference/rest/v1/mediaItems#MediaItem.
 */
export interface GPhotosMediaItem {
  /** URL to the media item's bytes. */
  baseUrl?: string;
  /** MIME type of the media item. */
  mimeType: string;
  /** Metadata related to the media item. */
  mediaMetadata: GPhotosMediaMetadata;
}

/** The response of /api/v1/gphotos/:id/media-items/:media-item-id */
export type GPhotosMediaItemDetailsApiResponse = GPhotosMediaItem;

@Injectable({ providedIn: 'root' })
export class WebApiService {
  private readonly httpClient = inject(HttpClient);

  /** Fetches the details of an album. */
  getAlbum(
    accessToken: string,
    albumId: string,
  ): Observable<Result<AlbumDetailsApiResponse>> {
    const url = `${environment.webApiEndpoint}/api/v1/albums/${albumId}`;
    return this.httpClient
      .get<AlbumDetailsApiResponse>(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
      .pipe(toResult());
  }

  /** Fetches the details of a media item. */
  getMediaItem(
    accessToken: string,
    mediaItemId: string,
  ): Observable<Result<MediaItemDetailsApiResponse>> {
    const url = `${environment.webApiEndpoint}/api/v1/media-items/${mediaItemId}`;
    return this.httpClient
      .get<MediaItemDetailsApiResponse>(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
      .pipe(toResult());
  }

  /** Fetches the details of a gphotos media item. */
  getGPhotosMediaItem(
    accessToken: string,
    gMediaItemId: string,
  ): Observable<Result<GPhotosMediaItemDetailsApiResponse>> {
    const url = `${environment.webApiEndpoint}/api/v1/gphotos/media-items/${gMediaItemId}`;
    return this.httpClient
      .get<GPhotosMediaItemDetailsApiResponse>(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
      .pipe(toResult());
  }

  /** Lists all the media items in a paginated way. */
  listMediaItems(
    accessToken: string,
    request: ListMediaItemsInAlbumRequest,
  ): Observable<Result<ListMediaItemsInAlbumResponse>> {
    const url = `${environment.webApiEndpoint}/api/v1/albums/${request.albumId}/media-items`;

    let params = new HttpParams();
    if (request.pageSize) {
      params = params.set('pageSize', request.pageSize);
    }
    if (request.pageToken) {
      params = params.set('pageToken', request.pageToken);
    }
    if (request.sortBy) {
      params = params.set('sortBy', request.sortBy.field);
      params = params.set('sortDir', request.sortBy.direction);
    }

    return this.httpClient
      .get<ListMediaItemsInAlbumResponse>(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        params,
      })
      .pipe(toResult());
  }
}
