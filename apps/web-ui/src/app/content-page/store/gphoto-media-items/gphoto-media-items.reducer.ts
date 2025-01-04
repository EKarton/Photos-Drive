import { createFeature, createReducer, on } from '@ngrx/store';

import { loadGPhotosMediaItemDetailsResult } from './gphoto-media-items.actions';
import { buildInitialState, FEATURE_KEY } from './gphoto-media-items.state';

export const gPhotosMediaItemsReducer = createReducer(
  buildInitialState(),

  on(
    loadGPhotosMediaItemDetailsResult,
    (state, { gPhotosMediaItemId, result }) => {
      return {
        ...state,
        idToDetails: state.idToDetails.set(gPhotosMediaItemId, result),
      };
    },
  ),
);

export const gPhotosMediaItemsFeature = createFeature({
  name: FEATURE_KEY,
  reducer: gPhotosMediaItemsReducer,
});
