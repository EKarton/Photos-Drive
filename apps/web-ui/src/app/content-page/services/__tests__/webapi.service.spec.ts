import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../../environments/environment';
import { toSuccess } from '../../../shared/results/results';
import {
  AlbumDetailsApiResponse,
  GPhotosMediaItemDetailsApiResponse,
  ListMediaItemsInAlbumRequest,
  ListMediaItemsInAlbumSortByFields,
  ListMediaItemsInAlbumSortDirection,
  MediaItemDetailsApiResponse,
  WebApiService,
} from '../webapi.service';

describe('WebApiService', () => {
  let service: WebApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        WebApiService,
      ],
    });
    service = TestBed.inject(WebApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('getAlbum()', () => {
    it('should fetch album details', () => {
      const albumId = 'album123';
      const mockResponse: AlbumDetailsApiResponse = {
        id: albumId,
        albumName: 'Test Album',
        childAlbumIds: [],
        mediaItemIds: ['media1', 'media2'],
      };

      service.getAlbum('authToken123', albumId).subscribe((response) => {
        expect(response).toEqual(toSuccess(mockResponse));
      });

      const req = httpMock.expectOne(
        `${environment.webApiEndpoint}/api/v1/albums/${albumId}`,
      );
      expect(req.request.method).toBe('GET');
      expect(req.request.headers.get('Authorization')).toEqual(
        'Bearer authToken123',
      );
      req.flush(mockResponse);
    });
  });

  describe('getMediaItem()', () => {
    it('should fetch media item details', () => {
      const mediaItemId = 'media123';
      const mockResponse: MediaItemDetailsApiResponse = {
        id: mediaItemId,
        fileName: 'test.jpg',
        hashCode: 'abc123',
        gPhotosMediaItemId: 'client1:gphoto123',
      };

      service
        .getMediaItem('authToken123', mediaItemId)
        .subscribe((response) => {
          expect(response).toEqual(toSuccess(mockResponse));
        });

      const req = httpMock.expectOne(
        `${environment.webApiEndpoint}/api/v1/media-items/${mediaItemId}`,
      );
      expect(req.request.method).toBe('GET');
      expect(req.request.headers.get('Authorization')).toEqual(
        'Bearer authToken123',
      );
      req.flush(mockResponse);
    });
  });

  describe('getGPhotosMediaItem', () => {
    it('should fetch GPhotos media item details', () => {
      const gMediaItemId = 'client1:gphoto123';
      const mockResponse: GPhotosMediaItemDetailsApiResponse = {
        baseUrl: 'https://example.com/media-item.jpg',
        mimeType: 'image/jpeg',
        mediaMetadata: {
          creationTime: '2025-01-01T00:00:00Z',
          width: '1920',
          height: '1080',
          photo: {
            cameraMake: 'Canon',
            cameraModel: 'EOS 5D Mark IV',
            focalLength: 50,
            apertureFNumber: 1.4,
            isoEquivalent: 800,
            exposureTime: '1/500s',
          },
        },
      };

      service
        .getGPhotosMediaItem('authToken123', gMediaItemId)
        .subscribe((response) => {
          expect(response).toEqual(toSuccess(mockResponse));
        });

      const req = httpMock.expectOne(
        `${environment.webApiEndpoint}/api/v1/gphotos/media-items/${gMediaItemId}`,
      );
      expect(req.request.method).toBe('GET');
      expect(req.request.headers.get('Authorization')).toEqual(
        'Bearer authToken123',
      );
      req.flush(mockResponse);
    });
  });

  describe('listMediaItems', () => {
    const accessToken = 'fake-token';
    const albumId = 'album123';

    it('should make a GET request to fetch media items with basic request', () => {
      const request: ListMediaItemsInAlbumRequest = { albumId };
      const mockResponse = {
        mediaItems: [
          {
            id: '1',
            fileName: 'photo.jpg',
            hashCode: 'abc',
            gPhotosMediaItemId: 'g1',
          },
        ],
        nextPageToken: 'next123',
      };

      service.listMediaItems(accessToken, request).subscribe((response) => {
        expect(response).toEqual(toSuccess(mockResponse));
      });

      const req = httpMock.expectOne(
        `${environment.webApiEndpoint}/api/v1/albums/${albumId}/media-items`,
      );

      expect(req.request.method).toBe('GET');
      expect(req.request.headers.get('Authorization')).toBe(
        `Bearer ${accessToken}`,
      );
      expect(req.request.params.keys()).toEqual([]);

      req.flush(mockResponse);
    });

    it('should include query params when provided', () => {
      const request: ListMediaItemsInAlbumRequest = {
        albumId,
        pageSize: 10,
        pageToken: 'page123',
        sortBy: {
          field: ListMediaItemsInAlbumSortByFields.ID,
          direction: ListMediaItemsInAlbumSortDirection.DESCENDING,
        },
      };

      const mockResponse = { mediaItems: [], nextPageToken: undefined };

      service.listMediaItems(accessToken, request).subscribe((response) => {
        expect(response).toEqual(toSuccess(mockResponse));
      });

      const req = httpMock.expectOne((req) => {
        return (
          req.url ===
            `${environment.webApiEndpoint}/api/v1/albums/${albumId}/media-items` &&
          req.params.get('pageSize') === '10' &&
          req.params.get('pageToken') === 'page123' &&
          req.params.get('sortBy') === 'id' &&
          req.params.get('sortDir') === 'desc'
        );
      });

      expect(req.request.method).toBe('GET');
      expect(req.request.headers.get('Authorization')).toBe(
        `Bearer ${accessToken}`,
      );

      req.flush(mockResponse);
    });
  });
});
