import { createFeature, createReducer, on } from '@ngrx/store';

import { loadMediaItemDetailsResult } from './media-items.actions';
import { buildInitialState, FEATURE_KEY } from './media-items.state';

export const mediaItemsReducer = createReducer(
  buildInitialState(),

  on(loadMediaItemDetailsResult, (state, { mediaItemId, result }) => {
    return {
      ...state,
      idToDetails: state.idToDetails.set(mediaItemId, result),
    };
  }),
);

export const mediaItemsFeature = createFeature({
  name: FEATURE_KEY,
  reducer: mediaItemsReducer,
});
