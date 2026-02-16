import { inject, Injectable } from '@angular/core';
import { SafeUrl } from '@angular/platform-browser';
import { ComponentStore } from '@ngrx/component-store';
import { Store } from '@ngrx/store';
import { switchMap, tap } from 'rxjs/operators';

import { authState } from '../../../../../auth/store';
import { Result, toPending } from '../../../../../shared/results/results';
import { WebApiService } from '../../../../services/web-api/web-api.service';

/** State definition for {@code ImageMapMarkerStore}. */
export interface ImageMapMarkerState {
  url: Result<SafeUrl>;
}

/** Initial state for {@code ImageMarkerStore}. */
export const INITIAL_STATE: ImageMapMarkerState = {
  url: toPending(),
};

/** Component store for {@code ImageComponent}. */
@Injectable()
export class ImageMapMarkerStore extends ComponentStore<ImageMapMarkerState> {
  private webApiService = inject(WebApiService);
  private store = inject(Store);

  constructor() {
    super(INITIAL_STATE);
  }

  readonly url = this.selectSignal((state) => state.url);

  readonly loadUrl = this.effect<string>((mediaItemId$) =>
    mediaItemId$.pipe(
      switchMap((mediaItemId) => {
        this.patchState({
          ...INITIAL_STATE,
        });

        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            return this.webApiService
              .getMediaItemImage(accessToken, mediaItemId)
              .pipe(
                tap((response) => {
                  this.patchState({
                    url: response,
                  });
                }),
              );
          }),
        );
      }),
    ),
  );
}
