import {
  HttpClient,
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
    mockCacheService.get.and.returnValue(
      new HttpResponse({
        body: 'My data',
        status: 200,
      }),
    );

    httpClient.get(testUrl).subscribe((res) => {
      expect(res).toEqual('My data');
      expect(mockCacheService.get).toHaveBeenCalledWith(testUrl);
      done();
    });
  });

  it('should call next() and cache the response if not cached', (done) => {
    mockCacheService.get.and.returnValue(undefined);

    httpClient.get(testUrl).subscribe((res) => {
      expect(res).toEqual('My data');
      expect(mockCacheService.get).toHaveBeenCalledWith(testUrl);
      expect(mockCacheService.set).toHaveBeenCalledWith(
        testUrl,
        jasmine.any(HttpResponse),
        60 * 60 * 1000,
      );
      done();
    });
    httpMock.expectOne(testUrl).flush('My data');
  });

  it('should skip caching for non-GET requests', (done) => {
    httpClient.post(testUrl, {}).subscribe((res) => {
      expect(res).toEqual('My data');
      expect(mockCacheService.get).not.toHaveBeenCalled();
      expect(mockCacheService.set).not.toHaveBeenCalled();
      done();
    });
    httpMock.expectOne(testUrl).flush('My data');
  });

  it('should skip caching for URLs outside webApiEndpoint', (done) => {
    httpClient.get('https://other.com/api/data').subscribe((res) => {
      expect(res).toEqual('My data');
      expect(mockCacheService.get).toHaveBeenCalledWith(
        'https://other.com/api/data',
      );
      expect(mockCacheService.set).toHaveBeenCalledTimes(0);
      done();
    });
    httpMock.expectOne(testUrl).flush('My data');
  });
});
