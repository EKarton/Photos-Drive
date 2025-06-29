import { createAction, props } from '@ngrx/store';

import { Result } from '../../../shared/results/results';
import { Album, AlbumDetailsApiResponse } from '../../services/types/album';

/** An action that fetches the details of an album. */
export const loadAlbumDetails = createAction(
  '[Albums] Load details of an album by ID',
  props<{ albumId: string }>(),
);

/** An action that saves the results of fetching a list of GPhotos clients */
export const addAlbumResult = createAction(
  '[Albums] Saves results of getting details of an album',
  props<{ albumId: string; result: Result<AlbumDetailsApiResponse> }>(),
);

/** An action that saves the details of an album to the store. */
export const addAlbum = createAction(
  '[Albums] Add an album to the store',
  props<{ album: Album }>(),
);
