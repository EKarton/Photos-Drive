import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Result } from '../../shared/results/results';
import { toResult } from '../../shared/results/rxjs/toResult';

export interface TokenResponse {
  accessToken: string;
  userProfileUrl: string;
  mapboxApiToken: string;
}

export interface GetGoogleLoginUrlResponse {
  url: string;
}

@Injectable({ providedIn: 'root' })
export class WebApiService {
  private readonly httpClient = inject(HttpClient);

  getGoogleLoginUrl(): Observable<Result<GetGoogleLoginUrlResponse>> {
    const url = `${environment.webApiEndpoint}/auth/v1/google/login?select_account=true`;
    return this.httpClient.get<GetGoogleLoginUrlResponse>(url).pipe(toResult());
  }

  fetchAccessToken(code: string, state: string): Observable<TokenResponse> {
    const url = `${environment.webApiEndpoint}/auth/v1/google/token`;
    return this.httpClient.post<TokenResponse>(
      url,
      { code, state },
      { withCredentials: true },
    );
  }
}
