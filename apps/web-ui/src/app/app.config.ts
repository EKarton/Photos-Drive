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
import { AlbumsEffects } from './content-page/store/albums/albums.effects';
import { albumsFeature } from './content-page/store/albums/albums.reducer';
import { GPhotosMediaItemsEffects } from './content-page/store/gphoto-media-items/gphoto-media-items.effects';
import { gPhotosMediaItemsFeature } from './content-page/store/gphoto-media-items/gphoto-media-items.reducer';
import { GPhotosClientsEffects } from './content-page/store/gphotos-clients/gphotos-clients.effects';
import { gPhotosClientsFeature } from './content-page/store/gphotos-clients/gphotos-clients.reducer';
import { MediaItemsEffects } from './content-page/store/media-items/media-items.effects';
import { mediaItemsFeature } from './content-page/store/media-items/media-items.reducer';
import { mediaViewerFeature } from './content-page/store/media-viewer/media-viewer.reducer';
import { ThemeEffects } from './themes/store/theme.effects';
import { themeFeature } from './themes/store/theme.reducer';

export const appConfig: ApplicationConfig = {
  providers: [
    provideAnimations(),
    provideHttpClient(withInterceptors([webApiAuthRequestInterceptor])),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideStore({}),

    provideState(themeFeature),
    provideState(authFeature),
    provideState(albumsFeature),
    provideState(gPhotosClientsFeature),
    provideState(mediaItemsFeature),
    provideState(gPhotosMediaItemsFeature),
    provideState(mediaViewerFeature),

    provideEffects(ThemeEffects),
    provideEffects(AuthEffects),
    provideEffects(AlbumsEffects),
    provideEffects(GPhotosClientsEffects),
    provideEffects(MediaItemsEffects),
    provideEffects(GPhotosMediaItemsEffects),

    provideStoreDevtools({ maxAge: 25, logOnly: !isDevMode() }),
  ],
};
