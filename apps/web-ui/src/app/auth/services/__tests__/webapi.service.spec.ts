import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../../environments/environment';
import { toSuccess } from '../../../shared/results/results';
import {
  GetGoogleLoginUrlResponse,
  TokenResponse,
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

  describe('getGoogleLoginUrl', () => {
    it('should get google login url', () => {
      const mockResponse: GetGoogleLoginUrlResponse = {
        url: 'mockGoogleLoginUrl',
      };

      service.getGoogleLoginUrl().subscribe((response) => {
        expect(response).toEqual(toSuccess(mockResponse));
      });

      const req = httpMock.expectOne(
        `${environment.webApiEndpoint}/auth/v1/google/login?select_account=true`,
      );

      expect(req.request.method).toBe('GET');

      req.flush(mockResponse);
    });
  });

  describe('fetchAccessToken', () => {
    it('should fetch access token', () => {
      const mockCode = 'test-auth-code';
      const mockState = 'test-state';
      const mockResponse: TokenResponse = {
        accessToken: 'mockAccessToken',
        userProfileUrl: 'mockUserProfileUrl',
        mapboxApiToken: 'mockMapboxApiToken',
      };

      service.fetchAccessToken(mockCode, mockState).subscribe((response) => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(
        `${environment.webApiEndpoint}/auth/v1/google/token`,
      );

      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ code: mockCode, state: mockState });

      req.flush(mockResponse);
    });

    it('should handle error response', () => {
      const mockCode = 'test-auth-code';
      const mockState = 'test-state';

      service.fetchAccessToken(mockCode, mockState).subscribe({
        next: () => fail('expected an error, not token'),
        error: (error) => {
          expect(error.status).toBe(500);
          expect(error.error).toContain('Server error');
        },
      });

      const req = httpMock.expectOne(
        `${environment.webApiEndpoint}/auth/v1/google/token`,
      );

      req.flush('Server error', {
        status: 500,
        statusText: 'Internal Server Error',
      });
    });
  });
});
