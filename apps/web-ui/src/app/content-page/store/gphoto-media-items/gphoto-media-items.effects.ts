import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { distinct, map, mergeMap, switchMap } from 'rxjs/operators';

import { authState } from '../../../auth/store';
import { toResult } from '../../../shared/results/rxjs/toResult';
import {
  GPhotosMediaItemDetailsApiResponse,
  WebApiService,
} from '../../services/webapi.service';
import * as gPhotosMediaItemsActions from './gphoto-media-items.actions';

@Injectable()
export class GPhotosMediaItemsEffects {
  private readonly actions$ = inject(Actions);
  private readonly store = inject(Store);
  private readonly webApiService = inject(WebApiService);

  loadGPhotosMediaItemDetails$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(gPhotosMediaItemsActions.loadGPhotosMediaItemDetails),
      distinct((prop) => prop.gMediaItemId),
      mergeMap(({ gMediaItemId }) => {
        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            return this.webApiService
              .fetchGPhotosMediaItemDetails(accessToken, gMediaItemId)
              .pipe(
                toResult<GPhotosMediaItemDetailsApiResponse>(),
                map((result) =>
                  gPhotosMediaItemsActions.loadGPhotosMediaItemDetailsResult({
                    gMediaItemId,
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
