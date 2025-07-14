import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Result } from '../../shared/results/results';
import { toResult } from '../../shared/results/rxjs/toResult';
import { AlbumDetailsApiResponse } from './types/album';
import { GPhotosMediaItemDetailsApiResponse } from './types/gphotos-media-item';
import { ListAlbumsRequest, ListAlbumsResponse } from './types/list-albums';
import {
  ListMediaItemsRequest,
  ListMediaItemsResponse,
  RawListMediaItemsResponse,
} from './types/list-media-items';
import { GetMapTileRequest, GetMapTileResponse } from './types/map-tile';
import {
  MediaItem,
  MediaItemDetailsApiResponse,
  RawMediaItemDetailsApiResponse,
} from './types/media-item';
import { RawMediaItem } from './types/media-item';

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
      .get<RawMediaItemDetailsApiResponse>(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
      .pipe(map(this.convertRawMediaItemToMediaItem), toResult());
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
    request: ListMediaItemsRequest,
  ): Observable<Result<ListMediaItemsResponse>> {
    const url = `${environment.webApiEndpoint}/api/v1/media-items`;

    let params = new HttpParams();
    if (request.albumId) {
      params = params.set('albumId', request.albumId);
    }
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
      .get<RawListMediaItemsResponse>(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        params,
      })
      .pipe(
        map((res) => ({
          mediaItems: res.mediaItems.map(this.convertRawMediaItemToMediaItem),
          nextPageToken: res.nextPageToken,
        })),
        toResult(),
      );
  }

  /** List albums in a paginated way. */
  listAlbums(
    accessToken: string,
    request: ListAlbumsRequest,
  ): Observable<Result<ListAlbumsResponse>> {
    const url = `${environment.webApiEndpoint}/api/v1/albums`;

    let params = new HttpParams();
    if (request.parentAlbumId) {
      params = params.set('parentAlbumId', request.parentAlbumId);
    }
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
      .get<ListAlbumsResponse>(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        params,
      })
      .pipe(toResult());
  }

  getMapTile(
    accessToken: string,
    request: GetMapTileRequest,
  ): Observable<Result<GetMapTileResponse>> {
    const url = `${environment.webApiEndpoint}/api/v1/map-tiles`;

    let params = new HttpParams();
    params = params.set('x', request.x);
    params = params.set('y', request.y);
    params = params.set('z', request.z);

    if (request.albumId) {
      params = params.set('album_id', request.albumId);
    }

    return this.httpClient
      .get<GetMapTileResponse>(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        params,
      })
      .pipe(toResult());
  }

  private convertRawMediaItemToMediaItem(rawDoc: RawMediaItem): MediaItem {
    return {
      id: rawDoc.id,
      fileName: rawDoc.fileName,
      hashCode: rawDoc.hashCode,
      gPhotosMediaItemId: rawDoc.gPhotosMediaItemId,
      location: rawDoc.location,
      width: rawDoc.width,
      height: rawDoc.height,
      dateTaken: new Date(rawDoc.dateTaken),
    };
  }
}
