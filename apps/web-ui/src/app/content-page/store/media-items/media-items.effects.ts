import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { distinct, map, mergeMap } from 'rxjs/operators';

import { toResult } from '../../../shared/results/rxjs/toResult';
import {
  MediaItemDetailsApiResponse,
  WebapiService,
} from '../../services/webapi.service';
import * as mediaItemsActions from './media-items.actions';

@Injectable()
export class MediaItemsEffects {
  private readonly actions$ = inject(Actions);
  private readonly webApiService = inject(WebapiService);

  loadMediaItemDetails$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(mediaItemsActions.loadMediaItemDetails),
      distinct((prop) => prop.mediaItemId),
      mergeMap(({ mediaItemId }) => {
        return this.webApiService.fetchMediaItemDetails(mediaItemId).pipe(
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
  });
}
