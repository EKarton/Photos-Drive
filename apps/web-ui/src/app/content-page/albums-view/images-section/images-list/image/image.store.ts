import { inject, Injectable } from '@angular/core';
import { ComponentStore } from '@ngrx/component-store';
import { Store } from '@ngrx/store';
import { switchMap, tap } from 'rxjs/operators';

import { authState } from '../../../../../auth/store';
import { Result, toPending } from '../../../../../shared/results/results';
import { GPhotosMediaItemDetailsApiResponse } from '../../../../services/types/gphotos-media-item';
import { GPhotosMediaItem } from '../../../../services/types/gphotos-media-item';
import { WebApiService } from '../../../../services/webapi.service';

/** State definition for {@code ImageStore}. */
export interface ImageState {
  gPhotosMediaItem: Result<GPhotosMediaItem>;
}

/** Initial state for {@code ImageStore}. */
export const INITIAL_STATE: ImageState = {
  gPhotosMediaItem: toPending(),
};

/** Component store for {@code ImageComponent}. */
@Injectable()
export class ImageStore extends ComponentStore<ImageState> {
  private webApiService = inject(WebApiService);
  private store = inject(Store);

  constructor() {
    super(INITIAL_STATE);
  }

  readonly gPhotosMediaItem = this.selectSignal(
    (state) => state.gPhotosMediaItem,
  );

  private readonly clearStates = this.updater(
    (): ImageState => ({
      ...INITIAL_STATE,
    }),
  );

  private readonly setGPhotosMediaItem = this.updater(
    (
      state: ImageState,
      response: Result<GPhotosMediaItemDetailsApiResponse>,
    ): ImageState => ({
      ...state,
      gPhotosMediaItem: response,
    }),
  );

  readonly loadGPhotosMediaItemDetails = this.effect<string>(
    (gPhotoMediaItemId$) =>
      gPhotoMediaItemId$.pipe(
        switchMap((gPhotosMediaItemId) => {
          this.clearStates();

          return this.store.select(authState.selectAuthToken).pipe(
            switchMap((accessToken) => {
              return this.webApiService
                .getGPhotosMediaItem(accessToken, gPhotosMediaItemId)
                .pipe(tap((response) => this.setGPhotosMediaItem(response)));
            }),
          );
        }),
      ),
  );
}
