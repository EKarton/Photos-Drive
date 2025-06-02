import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  ApplicationConfig,
  isDevMode,
  provideZoneChangeDetection,
} from '@angular/core';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideRouter } from '@angular/router';
import { provideEffects } from '@ngrx/effects';
import { provideState, provideStore } from '@ngrx/store';
import { provideStoreDevtools } from '@ngrx/store-devtools';

import { routes } from './app.routes';
import { AuthEffects } from './auth/store/auth.effects';
import { authFeature } from './auth/store/auth.reducer';
import { webApiAuthRequestInterceptor } from './content-page/interceptors/webapi-auth-request.interceptor';
import { webApiHttpCacheInterceptor } from './content-page/interceptors/webapi-cache.interceptor';
import { AlbumsEffects } from './content-page/store/albums/albums.effects';
import { albumsFeature } from './content-page/store/albums/albums.reducer';
import { mediaViewerFeature } from './content-page/store/media-viewer/media-viewer.reducer';
import { ThemeEffects } from './themes/store/theme.effects';
import { themeFeature } from './themes/store/theme.reducer';

export const appConfig: ApplicationConfig = {
  providers: [
    provideAnimations(),
    provideHttpClient(
      withInterceptors([
        webApiAuthRequestInterceptor,
        webApiHttpCacheInterceptor,
      ]),
    ),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideStore({}),

    provideState(themeFeature),
    provideState(authFeature),
    provideState(albumsFeature),
    provideState(mediaViewerFeature),

    provideEffects(ThemeEffects),
    provideEffects(AuthEffects),
    provideEffects(AlbumsEffects),

    provideStoreDevtools({ maxAge: 25, logOnly: !isDevMode() }),
  ],
};
