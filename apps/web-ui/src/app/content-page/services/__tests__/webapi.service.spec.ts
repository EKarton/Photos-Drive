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
  MediaItemDetailsApiResponse,
  RefreshTokenApiResponse,
  WebapiService,
} from '../webapi.service';

describe('WebapiService', () => {
  let service: WebapiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        WebapiService,
      ],
    });
    service = TestBed.inject(WebapiService);
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

    service.fetchGPhotosClients().subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(
      `${environment.webApiEndpoint}/api/v1/gphotos-clients`,
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.withCredentials).toBeTrue();
    req.flush(mockResponse);
  });

  it('should refresh GPhoto client access token', () => {
    const clientId = '123';
    const mockResponse: RefreshTokenApiResponse = { newToken: 'newToken123' };

    service.refreshGPhotoClientAccessToken(clientId).subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(
      `${environment.webApiEndpoint}/api/v1/gphotos-clients/${clientId}/token-refresh`,
    );
    expect(req.request.method).toBe('POST');
    expect(req.request.withCredentials).toBeTrue();
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

    service.fetchAlbumDetails(albumId).subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(
      `${environment.webApiEndpoint}/api/v1/albums/${albumId}`,
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.withCredentials).toBeTrue();
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

    service.fetchMediaItemDetails(mediaItemId).subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(
      `${environment.webApiEndpoint}/api/v1/media-items/${mediaItemId}`,
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.withCredentials).toBeTrue();
    req.flush(mockResponse);
  });
});
