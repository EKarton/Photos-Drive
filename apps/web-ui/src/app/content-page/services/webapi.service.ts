import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

/** Represents a GPhotos client. */
export interface GPhotosClient {
  id: string;
  token: string;
}

/** Represents the api response returned from {@code fetchGPhotosClients()} */
export interface GPhotosClientsListApiResponse {
  gphotoClients: GPhotosClient[];
}

/** Represents an album. */
export interface Album {
  id: string;
  albumName: string;
  parentAlbumId?: string;
  childAlbumIds: string[];
  mediaItemIds: string[];
}

/** Represents the api response returned from {@code fetchAlbumDetails()} */
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
  gPhotosClientId: string;
  gPhotosMediaItemId: string;
}

export type MediaItemDetailsApiResponse = MediaItem;

export interface RefreshTokenApiResponse {
  newToken: string;
}

@Injectable({ providedIn: 'root' })
export class WebApiService {
  private readonly httpClient = inject(HttpClient);

  /** Fetches a list of GPhotos clients */
  fetchGPhotosClients(
    accessToken: string,
  ): Observable<GPhotosClientsListApiResponse> {
    const url = `${environment.webApiEndpoint}/api/v1/gphotos-clients`;
    return this.httpClient.get<GPhotosClientsListApiResponse>(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }

  refreshGPhotoClientAccessToken(
    accessToken: string,
    clientId: string,
  ): Observable<RefreshTokenApiResponse> {
    const url = `${environment.webApiEndpoint}/api/v1/gphotos-clients/${clientId}/token-refresh`;
    const options = {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    };
    return this.httpClient.post<RefreshTokenApiResponse>(url, null, options);
  }

  /** Fetches the details of an album. */
  fetchAlbumDetails(
    accessToken: string,
    albumId: string,
  ): Observable<AlbumDetailsApiResponse> {
    const url = `${environment.webApiEndpoint}/api/v1/albums/${albumId}`;
    return this.httpClient.get<AlbumDetailsApiResponse>(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }

  /** Fetches the details of a media item. */
  fetchMediaItemDetails(
    accessToken: string,
    mediaItemId: string,
  ): Observable<MediaItemDetailsApiResponse> {
    const url = `${environment.webApiEndpoint}/api/v1/media-items/${mediaItemId}`;
    return this.httpClient.get<MediaItemDetailsApiResponse>(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }
}
