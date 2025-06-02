import {
  HttpClient,
  HttpRequest,
  HttpResponse,
  provideHttpClient,
  withInterceptors,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../../environments/environment';
import { HttpCacheService } from '../http-cache.service';
import { webApiHttpCacheInterceptor } from '../webapi-cache.interceptor';

describe('webApiHttpCacheInterceptor', () => {
  let mockCacheService: jasmine.SpyObj<HttpCacheService>;
  let httpClient: HttpClient;
  let httpMock: HttpTestingController;

  const testUrl = `${environment.webApiEndpoint}/api/v1/albums/123/media-items`;
  const mockResponse = new HttpResponse({
    body: { message: 'ok' },
    status: 200,
  });

  beforeEach(() => {
    mockCacheService = jasmine.createSpyObj<HttpCacheService>(
      'HttpCacheService',
      ['get', 'set'],
    );

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([webApiHttpCacheInterceptor])),
        provideHttpClientTesting(),
        { provide: HttpCacheService, useValue: mockCacheService },
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('should return cached response if available', (done) => {
    mockCacheService.get.and.returnValue(mockResponse);

    httpClient.get(testUrl).subscribe((res) => {
      expect(res).toEqual(mockResponse);
      expect(mockCacheService.get).toHaveBeenCalledWith(testUrl);
      done();
    });
  });

  it('should call next() and cache the response if not cached', (done) => {
    mockCacheService.get.and.returnValue(undefined);

    httpClient.get(testUrl).subscribe((res) => {
      expect(res).toEqual(mockResponse);
      expect(mockCacheService.get).toHaveBeenCalledWith(testUrl);
      expect(mockCacheService.set).toHaveBeenCalledWith(
        testUrl,
        jasmine.any(HttpResponse),
        10 * 60 * 1000,
      );
      done();
    });
    httpMock.expectOne(testUrl).flush(mockResponse);
  });

  it('should skip caching for non-GET requests', (done) => {
    httpClient.post(testUrl, {}).subscribe((res) => {
      expect(res).toBe(mockResponse);
      expect(mockCacheService.get).not.toHaveBeenCalled();
      expect(mockCacheService.set).not.toHaveBeenCalled();
      done();
    });
    httpMock.expectOne(testUrl).flush(mockResponse);
  });

  it('should skip caching for URLs outside webApiEndpoint', (done) => {
    httpClient.get(testUrl).subscribe((res) => {
      expect(res).toBe(mockResponse);
      expect(mockCacheService.get).not.toHaveBeenCalled();
      expect(mockCacheService.set).not.toHaveBeenCalled();
      done();
    });
    httpMock.expectOne(testUrl).flush(mockResponse);
  });

  it('should use correct TTL based on URL', (done) => {
    mockCacheService.get.and.returnValue(undefined);

    const configUrl = `${environment.webApiEndpoint}/api/v1/config`;
    httpClient.get(configUrl).subscribe(() => {
      expect(mockCacheService.set).toHaveBeenCalledWith(
        configUrl,
        jasmine.any(HttpResponse),
        60 * 60 * 1000, // 1 hour
      );
      done();
    });
  });
});
