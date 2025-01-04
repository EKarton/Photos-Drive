import { createAction, props } from '@ngrx/store';

import { Result } from '../../../shared/results/results';
import { MediaItemDetailsApiResponse } from '../../services/webapi.service';

/** An action that fetches the details of a media item. */
export const loadMediaItemDetails = createAction(
  '[Media Items] Load details of a media item by ID',
  props<{ mediaItemId: string }>(),
);

/** An action that saves the results of fetching the details of a media item. */
export const loadMediaItemDetailsResult = createAction(
  '[Media Items] Saves results of getting details of a media item',
  props<{ mediaItemId: string; result: Result<MediaItemDetailsApiResponse> }>(),
);
