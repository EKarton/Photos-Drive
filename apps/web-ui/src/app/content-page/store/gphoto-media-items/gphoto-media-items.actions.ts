import { createAction, props } from '@ngrx/store';

import { Result } from '../../../shared/results/results';
import { GPhotosMediaItem } from '../../services/webapi.service';

/** An action that fetches the details of a media item. */
export const loadGPhotosMediaItemDetails = createAction(
  '[GPhotos Media Items] Load details of a media item from GPhotos by ID',
  props<{ gPhotosMediaItemId: string }>(),
);

/** An action that saves the results of fetching the details of a media item. */
export const loadGPhotosMediaItemDetailsResult = createAction(
  '[GPhotos Media Items] Saves results of getting details of a media item from GPhotos',
  props<{
    gPhotosMediaItemId: string;
    result: Result<GPhotosMediaItem>;
  }>(),
);
