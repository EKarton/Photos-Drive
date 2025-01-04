import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import {
  GhotosApiService,
  GPhotosMediaItemApiResponse,
} from '../gphotos-api.service';

describe('GhotosApiService', () => {
  let service: GhotosApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        GhotosApiService,
      ],
    });
    service = TestBed.inject(GhotosApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch media item details', () => {
    const mockToken = 'mock-token';
    const mockMediaItemId = 'mock-media-item-id';
    const mockResponse: GPhotosMediaItemApiResponse = {
      id: mockMediaItemId,
      description: 'Test description',
      productUrl: 'https://photos.google.com/test',
      baseUrl: 'https://lh3.googleusercontent.com/test',
      mimeType: 'image/jpeg',
      mediaMetadata: {
        creationTime: '2023-01-01T00:00:00Z',
        width: 1920,
        height: 1080,
      },
      contributorInfo: {
        profilePictureBaseUrl: 'https://lh3.googleusercontent.com/contributor',
        displayName: 'Test User',
      },
      filename: 'test_image.jpg',
    };

    service
      .fetchMediaItemDetail(mockToken, mockMediaItemId)
      .subscribe((response) => {
        expect(response).toEqual(mockResponse);
      });

    const req = httpMock.expectOne(
      `https://photoslibrary.googleapis.com/v1/mediaItems/${mockMediaItemId}`,
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('Authorization')).toBe(
      `Bearer ${mockToken}`,
    );
    req.flush(mockResponse);
  });

  it('should handle error when fetching media item details', () => {
    const mockToken = 'mock-token';
    const mockMediaItemId = 'mock-media-item-id';
    const mockError = { status: 404, statusText: 'Not Found' };

    service.fetchMediaItemDetail(mockToken, mockMediaItemId).subscribe({
      next: () => fail('should have failed with 404 error'),
      error: (error) => {
        expect(error.status).toBe(404);
        expect(error.statusText).toBe('Not Found');
      },
    });

    const req = httpMock.expectOne(
      `https://photoslibrary.googleapis.com/v1/mediaItems/${mockMediaItemId}`,
    );
    expect(req.request.method).toBe('GET');
    req.flush('', mockError);
  });
});
