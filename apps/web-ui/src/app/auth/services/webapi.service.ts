import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface TokenResponse {
  accessToken: string;
  userProfileUrl: string;
  mapboxApiToken: string;
}

@Injectable({ providedIn: 'root' })
export class WebApiService {
  private readonly httpClient = inject(HttpClient);

  fetchAccessToken(code: string): Observable<TokenResponse> {
    const url = `${environment.webApiEndpoint}/auth/v1/google/token`;
    return this.httpClient.post<TokenResponse>(url, {
      code,
    });
  }
}
