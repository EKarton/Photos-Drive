import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { EMPTY, Observable, pipe, throwError, UnaryFunction } from 'rxjs';
import { catchError, distinct, map, mergeMap, switchMap } from 'rxjs/operators';

import { Result } from '../../../shared/results/results';
import { filterOnlySuccess } from '../../../shared/results/rxjs/filterOnlySuccess';
import { toResult } from '../../../shared/results/rxjs/toResult';
import {
  GhotosApiService,
  GPhotosMediaItemApiResponse,
} from '../../services/gphotos-api.service';
import * as gPhotosClientsActions from '../gphotos-clients/gphotos-clients.actions';
import * as gPhotosClientsState from '../gphotos-clients/gphotos-clients.state';
import * as gPhotosMediaItemsActions from './gphoto-media-items.actions';

@Injectable()
export class GPhotosMediaItemsEffects {
  private readonly actions$ = inject(Actions);
  private readonly store = inject(Store);
  private readonly gPhotosApi = inject(GhotosApiService);

  loadGPhotosMediaItemDetails$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(gPhotosMediaItemsActions.loadGPhotosMediaItemDetails),
      distinct((prop) => prop.gPhotosMediaItemId),
      mergeMap(({ gPhotosMediaItemId }) => {
        return this.fetchMediaItemDetail(gPhotosMediaItemId).pipe(
          map((result) =>
            gPhotosMediaItemsActions.loadGPhotosMediaItemDetailsResult({
              gPhotosMediaItemId,
              result,
            }),
          ),
        );
      }),
    );
  });

  private fetchMediaItemDetail(
    gPhotosMediaItemId: string,
  ): Observable<Result<GPhotosMediaItemApiResponse>> {
    const parts = gPhotosMediaItemId.split(':');
    const gClientId = parts[0];
    const gMediaItemId = parts[1];

    return this.store.select(gPhotosClientsState.selectToken(gClientId)).pipe(
      filterOnlySuccess(),
      switchMap((token) => {
        return this.gPhotosApi
          .fetchMediaItemDetail(token, gMediaItemId)
          .pipe(
            this.refreshTokenWhenExpired(gClientId),
            toResult<GPhotosMediaItemApiResponse>(),
          );
      }),
    );
  }

  private refreshTokenWhenExpired<T>(
    clientId: string,
  ): UnaryFunction<Observable<T>, Observable<T>> {
    return pipe(
      catchError((error) => {
        if (error instanceof HttpErrorResponse && error.status === 401) {
          this.store.dispatch(gPhotosClientsActions.refreshToken({ clientId }));
          return EMPTY;
        }

        return throwError(() => error);
      }),
    );
  }
}
