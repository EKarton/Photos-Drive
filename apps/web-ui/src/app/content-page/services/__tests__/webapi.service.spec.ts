import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../../environments/environment';
import {
  AlbumDetailsApiResponse,
  GPhotosClientsListApiResponse,
  GPhotosMediaItemDetailsApiResponse,
  MediaItemDetailsApiResponse,
  RefreshTokenApiResponse,
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

  it('should fetch GPhotos clients', () => {
    const mockResponse: GPhotosClientsListApiResponse = {
      gphotoClients: [
        { id: '1', token: 'token1' },
        { id: '2', token: 'token2' },
      ],
    };

    service.fetchGPhotosClients('authToken123').subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(
      `${environment.webApiEndpoint}/api/v1/gphotos-clients`,
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('Authorization')).toEqual(
      'Bearer authToken123',
    );
    req.flush(mockResponse);
  });

  it('should refresh GPhoto client access token', () => {
    const clientId = '123';
    const mockResponse: RefreshTokenApiResponse = { newToken: 'newToken123' };

    service
      .refreshGPhotoClientAccessToken('authToken123', clientId)
      .subscribe((response) => {
        expect(response).toEqual(mockResponse);
      });

    const req = httpMock.expectOne(
      `${environment.webApiEndpoint}/api/v1/gphotos-clients/${clientId}/token-refresh`,
    );
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('Authorization')).toEqual(
      'Bearer authToken123',
    );
    req.flush(mockResponse);
  });

  it('should fetch album details', () => {
    const albumId = 'album123';
    const mockResponse: AlbumDetailsApiResponse = {
      id: albumId,
      albumName: 'Test Album',
      childAlbumIds: [],
      mediaItemIds: ['media1', 'media2'],
    };

    service.fetchAlbumDetails('authToken123', albumId).subscribe((response) => {
      expect(response).toEqual(mockResponse);
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

  it('should fetch media item details', () => {
    const mediaItemId = 'media123';
    const mockResponse: MediaItemDetailsApiResponse = {
      id: mediaItemId,
      fileName: 'test.jpg',
      hashCode: 'abc123',
      gPhotosClientId: 'client1',
      gPhotosMediaItemId: 'gphoto123',
    };

    service
      .fetchMediaItemDetails('authToken123', mediaItemId)
      .subscribe((response) => {
        expect(response).toEqual(mockResponse);
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
      .fetchGPhotosMediaItemDetails('authToken123', gMediaItemId)
      .subscribe((response) => {
        expect(response).toEqual(mockResponse);
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
