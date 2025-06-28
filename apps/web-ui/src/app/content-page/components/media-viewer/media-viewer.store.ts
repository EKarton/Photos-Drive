import { inject, Injectable } from '@angular/core';
import { ComponentStore } from '@ngrx/component-store';
import { Store } from '@ngrx/store';
import { switchMap, tap } from 'rxjs/operators';

import { authState } from '../../../auth/store';
import { Result, toPending } from '../../../shared/results/results';
import { switchMapResultToResultRxJs } from '../../../shared/results/rxjs/switchMapResultToResultRxJs';
import { GPhotosMediaItemDetailsApiResponse } from '../../services/types/gphoto-media-item';
import { GPhotosMediaItem } from '../../services/types/gphoto-media-item';
import { MediaItemDetailsApiResponse } from '../../services/types/media-item';
import { MediaItem } from '../../services/types/media-item';
import { WebApiService } from '../../services/webapi.service';

/** The state definition for {@code MediaViewerStore} */
export interface MediaViewerState {
  mediaItemResult: Result<MediaItem>;
  gMediaItemResult: Result<GPhotosMediaItem>;
}

/** The initial state for the {@code MediaViewerStore} */
export const INITIAL_STATE: MediaViewerState = {
  mediaItemResult: toPending(),
  gMediaItemResult: toPending(),
};

/** A component store for the {@code MediaViewerComponent} */
@Injectable()
export class MediaViewerStore extends ComponentStore<MediaViewerState> {
  private readonly store = inject(Store);
  private readonly webApiService = inject(WebApiService);

  constructor() {
    super(INITIAL_STATE);
  }

  readonly mediaItemResult = this.selectSignal(
    (state) => state.mediaItemResult,
  );
  readonly gMediaItemResult = this.selectSignal(
    (state) => state.gMediaItemResult,
  );

  private readonly clearStates = this.updater(
    (): MediaViewerState => ({
      ...INITIAL_STATE,
    }),
  );

  private readonly setMediaItemResult = this.updater(
    (
      state: MediaViewerState,
      response: Result<MediaItemDetailsApiResponse>,
    ): MediaViewerState => ({
      ...state,
      mediaItemResult: response,
    }),
  );

  private readonly setGMediaItemResult = this.updater(
    (
      state: MediaViewerState,
      response: Result<GPhotosMediaItemDetailsApiResponse>,
    ): MediaViewerState => ({
      ...state,
      gMediaItemResult: response,
    }),
  );

  readonly loadDetails = this.effect<string>((mediaItemId$) =>
    mediaItemId$.pipe(
      switchMap((mediaItemId) => {
        this.clearStates();

        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            return this.webApiService
              .getMediaItem(accessToken, mediaItemId)
              .pipe(
                tap((mediaItemResult) =>
                  this.setMediaItemResult(mediaItemResult),
                ),
                switchMapResultToResultRxJs((mediaItem) => {
                  return this.webApiService
                    .getGPhotosMediaItem(
                      accessToken,
                      mediaItem.gPhotosMediaItemId,
                    )
                    .pipe(
                      tap((gMediaItemResult) =>
                        this.setGMediaItemResult(gMediaItemResult),
                      ),
                    );
                }),
              );
          }),
        );
      }),
    ),
  );
}
