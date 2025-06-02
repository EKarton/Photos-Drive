import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { of } from 'rxjs';
import { tap } from 'rxjs/operators';

import { environment } from '../../../environments/environment';
import { HttpCacheService } from './http-cache.service';

export const webApiHttpCacheInterceptor: HttpInterceptorFn = (req, next) => {
  const cacheService = inject(HttpCacheService);

  // Only cache GET requests
  if (req.method !== 'GET') {
    return next(req);
  }

  // Only cache web api endpoints
  if (!req.url.startsWith(environment.webApiEndpoint)) {
    return next(req);
  }

  const cachedResponse = cacheService.get(req.urlWithParams);
  if (cachedResponse) {
    console.log(`Cache hit: ${req.url}`);
    return of(cachedResponse);
  }

  return next(req).pipe(
    tap((event) => {
      if (event instanceof HttpResponse) {
        const ttl = getTTLForUrl(req.urlWithParams);
        cacheService.set(req.urlWithParams, event, ttl);
      }
    }),
  );
};

// TTL logic — customize this per endpoint
function getTTLForUrl(url: string): number {
  if (url.includes('/api/v1/albums')) return 10 * 60 * 1000; // 10 min
  if (url.includes('/api/v1/config')) return 60 * 60 * 1000; // 1 hour
  return 5 * 60 * 1000; // default: 5 min
}
