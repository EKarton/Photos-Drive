import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import {
  distinctUntilKeyChanged,
  map,
  mergeMap,
  switchMap,
} from 'rxjs/operators';

import { toResult } from '../../../shared/results/rxjs/toResult';
import {
  GPhotosClientsListApiResponse,
  RefreshTokenApiResponse,
  WebapiService,
} from '../../services/webapi.service';
import * as gPhotosClientsActions from './gphotos-clients.actions';

@Injectable()
export class GPhotosClientsEffects {
  private readonly actions$ = inject(Actions);
  private readonly webApiService = inject(WebapiService);

  loadGPhotosClients$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(gPhotosClientsActions.loadGPhotoClients),
      switchMap(() => {
        return this.webApiService.fetchGPhotosClients().pipe(
          toResult<GPhotosClientsListApiResponse>(),
          map((result) =>
            gPhotosClientsActions.loadGPhotoClientsResults({ result }),
          ),
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
        return this.webApiService.refreshGPhotoClientAccessToken(clientId).pipe(
          toResult<RefreshTokenApiResponse>(),
          map((result) =>
            gPhotosClientsActions.loadRefreshTokenResult({ clientId, result }),
          ),
        );
      }),
    );
  });
}
