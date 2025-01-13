import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { distinct, map, mergeMap, switchMap } from 'rxjs/operators';

import { authState } from '../../../auth/store';
import { toResult } from '../../../shared/results/rxjs/toResult';
import {
  MediaItemDetailsApiResponse,
  WebApiService,
} from '../../services/webapi.service';
import * as mediaItemsActions from './media-items.actions';

@Injectable()
export class MediaItemsEffects {
  private readonly store = inject(Store);
  private readonly actions$ = inject(Actions);
  private readonly webApiService = inject(WebApiService);

  loadMediaItemDetails$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(mediaItemsActions.loadMediaItemDetails),
      distinct((prop) => prop.mediaItemId),
      mergeMap(({ mediaItemId }) => {
        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            return this.webApiService
              .fetchMediaItemDetails(accessToken, mediaItemId)
              .pipe(
                toResult<MediaItemDetailsApiResponse>(),
                map((result) =>
                  mediaItemsActions.loadMediaItemDetailsResult({
                    mediaItemId,
                    result,
                  }),
                ),
              );
          }),
        );
      }),
    );
  });
}
