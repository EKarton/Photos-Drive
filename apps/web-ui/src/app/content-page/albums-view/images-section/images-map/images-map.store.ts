import { inject, Injectable } from '@angular/core';
import { ComponentStore } from '@ngrx/component-store';
import { Store } from '@ngrx/store';
import { delay, EMPTY, expand, switchMap, tap, withLatestFrom } from 'rxjs';

import { authState } from '../../../../auth/store';
import {
  hasSucceed,
  isPending,
  Result,
  toPending,
} from '../../../../shared/results/results';
import { combineResults2 } from '../../../../shared/results/utils/combineResults2';
import { mapResult } from '../../../../shared/results/utils/mapResult';
import { takeSuccessfulDataOrElse } from '../../../../shared/results/utils/takeSuccessfulDataOrElse';
import {
  ListMediaItemsRequest,
  ListMediaItemsResponse,
} from '../../../services/types/list-media-items';
import { MediaItem } from '../../../services/types/media-item';
import { WebApiService } from '../../../services/webapi.service';

export interface ImagesMapState {
  albumId: string;
  imagesResult: Result<MediaItem[]>;
  isFetchingImages: boolean;
}

export const INITIAL_STATE: ImagesMapState = {
  albumId: '',
  imagesResult: toPending(),
  isFetchingImages: false,
};

export interface LoadImagesRequest {
  albumId: string;
  pageSize?: number;
  delayBetweenPages?: number;
}

export const DEFAULT_DELAY_BETWEEN_PAGES = 150;

@Injectable()
export class ImagesMapStore extends ComponentStore<ImagesMapState> {
  private webApiService = inject(WebApiService);
  private store = inject(Store);

  constructor() {
    super(INITIAL_STATE);
  }

  readonly isFetchingImages = this.selectSignal(
    (state) => state.isFetchingImages,
  );
  readonly images = this.selectSignal((state) => state.imagesResult);

  readonly loadImages = this.effect<LoadImagesRequest>((request$) =>
    request$.pipe(
      withLatestFrom(this.state$),
      switchMap(([request]) => {
        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            const apiRequest: ListMediaItemsRequest = {
              albumId: request.albumId,
              pageSize: request.pageSize,
            };

            this.patchState({
              albumId: request.albumId,
              imagesResult: toPending(),
              isFetchingImages: true,
            });

            return this.webApiService
              .listMediaItems(accessToken, apiRequest)
              .pipe(
                expand((response) => {
                  if (!hasSucceed(response)) {
                    return EMPTY;
                  }

                  if (!response.data?.nextPageToken) {
                    return EMPTY;
                  }

                  const newApiRequest: ListMediaItemsRequest = {
                    ...apiRequest,
                    pageToken: response.data?.nextPageToken,
                  };

                  return this.webApiService
                    .listMediaItems(accessToken, newApiRequest)
                    .pipe(
                      delay(
                        request.delayBetweenPages ??
                          DEFAULT_DELAY_BETWEEN_PAGES,
                      ),
                    );
                }),
                tap((response: Result<ListMediaItemsResponse>) => {
                  this.addResponse(response);
                }),
              );
          }),
        );
      }),
    ),
  );

  private readonly addResponse = this.updater(
    (
      state: ImagesMapState,
      response: Result<ListMediaItemsResponse>,
    ): ImagesMapState => {
      if (isPending(response)) {
        return state;
      }

      if (isPending(state.imagesResult)) {
        return {
          ...state,
          imagesResult: mapResult(response, (page) => page.mediaItems),
          isFetchingImages: true,
        };
      }

      return {
        ...state,
        imagesResult: combineResults2(
          state.imagesResult,
          response,
          (prev, cur) => [...prev, ...cur.mediaItems],
        ),
        isFetchingImages: takeSuccessfulDataOrElse(
          mapResult(response, (cur) => cur.nextPageToken !== undefined),
          true,
        ),
      };
    },
  );
}
