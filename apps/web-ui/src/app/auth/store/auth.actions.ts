import { createAction, props } from '@ngrx/store';

import { Result } from '../../shared/results/results';
import { TokenResponse } from '../services/webapi.service';

/** An action that fetches the details of an album. */
export const loadAuth = createAction(
  '[Auth] Load auth details from auth code',
  props<{ code: string }>(),
);

/** An action that saves the results of fetching a list of GPhotos clients */
export const loadAuthResult = createAction(
  '[Auth] Saves results of getting auth details of a user',
  props<{ result: Result<TokenResponse> }>(),
);
