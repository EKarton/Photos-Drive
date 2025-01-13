import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import {
  distinctUntilKeyChanged,
  map,
  mergeMap,
  switchMap,
} from 'rxjs/operators';

import { authState } from '../../../auth/store';
import { toResult } from '../../../shared/results/rxjs/toResult';
import {
  GPhotosClientsListApiResponse,
  RefreshTokenApiResponse,
  WebApiService,
} from '../../services/webapi.service';
import * as gPhotosClientsActions from './gphotos-clients.actions';

@Injectable()
export class GPhotosClientsEffects {
  private readonly store = inject(Store);
  private readonly actions$ = inject(Actions);
  private readonly webApiService = inject(WebApiService);

  loadGPhotosClients$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(gPhotosClientsActions.loadGPhotoClients),
      switchMap(() => {
        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            return this.webApiService.fetchGPhotosClients(accessToken).pipe(
              toResult<GPhotosClientsListApiResponse>(),
              map((result) =>
                gPhotosClientsActions.loadGPhotoClientsResults({ result }),
              ),
            );
          }),
        );
      }),
    );
  });

  loadRefreshToken$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(gPhotosClientsActions.refreshToken),
      distinctUntilKeyChanged('clientId'),
      mergeMap(({ clientId }) => {
        console.log('Requesting to refresh access token');
        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            return this.webApiService
              .refreshGPhotoClientAccessToken(accessToken, clientId)
              .pipe(
                toResult<RefreshTokenApiResponse>(),
                map((result) =>
                  gPhotosClientsActions.loadRefreshTokenResult({
                    clientId,
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
