import { createAction, props } from '@ngrx/store';

import { Result } from '../../../shared/results/results';
import { AlbumDetailsApiResponse } from '../../services/webapi.service';

/** An action that fetches the details of an album. */
export const loadAlbumDetails = createAction(
  '[Albums] Load details of an album by ID',
  props<{ albumId: string }>(),
);

/** An action that saves the results of fetching a list of GPhotos clients */
export const loadAlbumDetailsResult = createAction(
  '[Albums] Saves results of getting details of an album',
  props<{ albumId: string; result: Result<AlbumDetailsApiResponse> }>(),
);
