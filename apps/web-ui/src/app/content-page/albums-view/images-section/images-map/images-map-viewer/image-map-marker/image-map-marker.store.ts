import { inject, Injectable } from '@angular/core';
import { ComponentStore } from '@ngrx/component-store';
import { Store } from '@ngrx/store';
import { switchMap, tap } from 'rxjs/operators';

import { authState } from '../../../../../../auth/store';
import { Result, toPending } from '../../../../../../shared/results/results';
import {
  GPhotosMediaItem,
  GPhotosMediaItemDetailsApiResponse,
} from '../../../../../services/types/gphotos-media-item';
import { WebApiService } from '../../../../../services/webapi.service';
import { ImageState } from '../../../images-list/image/image.store';

/** State definition for {@code ImageMapMarkerStore}. */
export interface ImageMapMarker {
  gPhotosMediaItem: Result<GPhotosMediaItem>;
}

/** Initial state for {@code ImageMarkerStore}. */
export const INITIAL_STATE: ImageMapMarker = {
  gPhotosMediaItem: toPending(),
};

/** Component store for {@code ImageComponent}. */
@Injectable()
export class ImageMapMarkerStore extends ComponentStore<ImageMapMarker> {
  private webApiService = inject(WebApiService);
  private store = inject(Store);

  constructor() {
    super(INITIAL_STATE);
  }

  readonly gPhotosMediaItem = this.selectSignal(
    (state) => state.gPhotosMediaItem,
  );

  readonly loadGPhotosMediaItemDetails = this.effect<string>(
    (gPhotoMediaItemId$) =>
      gPhotoMediaItemId$.pipe(
        switchMap((gPhotosMediaItemId) => {
          this.patchState({
            ...INITIAL_STATE,
          });

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

  private readonly setGPhotosMediaItem = this.updater(
    (
      state: ImageState,
      response: Result<GPhotosMediaItemDetailsApiResponse>,
    ): ImageState => ({
      ...state,
      gPhotosMediaItem: response,
    }),
  );
}
