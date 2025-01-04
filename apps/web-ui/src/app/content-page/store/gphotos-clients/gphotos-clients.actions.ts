import { createAction, props } from '@ngrx/store';

import { Result } from '../../../shared/results/results';
import {
  GPhotosClientsListApiResponse,
  RefreshTokenApiResponse,
} from '../../services/webapi.service';

/** An action that fetches a list of GPhotos clients. */
export const loadGPhotoClients = createAction(
  '[GPhotoClients] Load GPhoto clients',
);

/** An action that saves the results of fetching a list of GPhotos clients */
export const loadGPhotoClientsResults = createAction(
  '[GPhotoClients] Load GPhoto clients api success',
  props<{ result: Result<GPhotosClientsListApiResponse> }>(),
);

/** An action that refreshes the access token for a client. */
export const refreshToken = createAction(
  '[GPhotoClients] Refresh token',
  props<{ clientId: string }>(),
);

/** An action that saves the access token for a client. */
export const loadRefreshTokenResult = createAction(
  '[GPhotoClients] Loads new refresh token',
  props<{ clientId: string; result: Result<RefreshTokenApiResponse> }>(),
);
