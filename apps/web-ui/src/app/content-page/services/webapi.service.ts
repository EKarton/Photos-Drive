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
export class WebapiService {
  private readonly httpClient = inject(HttpClient);

  /** Fetches a list of GPhotos clients */
  fetchGPhotosClients(): Observable<GPhotosClientsListApiResponse> {
    const url = `${environment.webApiEndpoint}/api/v1/gphotos-clients`;
    return this.httpClient.get<GPhotosClientsListApiResponse>(url, {
      withCredentials: true,
    });
  }

  refreshGPhotoClientAccessToken(
    clientId: string,
  ): Observable<RefreshTokenApiResponse> {
    const url = `${environment.webApiEndpoint}/api/v1/gphotos-clients/${clientId}/token-refresh`;
    const options = {
      withCredentials: true,
    };
    return this.httpClient.post<RefreshTokenApiResponse>(url, null, options);
  }

  /** Fetches the details of an album. */
  fetchAlbumDetails(albumId: string): Observable<AlbumDetailsApiResponse> {
    const url = `${environment.webApiEndpoint}/api/v1/albums/${albumId}`;
    return this.httpClient.get<AlbumDetailsApiResponse>(url, {
      withCredentials: true,
    });
  }

  /** Fetches the details of a media item. */
  fetchMediaItemDetails(
    mediaItemId: string,
  ): Observable<MediaItemDetailsApiResponse> {
    const url = `${environment.webApiEndpoint}/api/v1/media-items/${mediaItemId}`;
    return this.httpClient.get<MediaItemDetailsApiResponse>(url, {
      withCredentials: true,
    });
  }
}
