import { createFeatureSelector, createSelector } from '@ngrx/store';
import { Map as ImmutableMap } from 'immutable';

import { Result, toPending } from '../../../shared/results/results';
import { MediaItem } from '../../services/webapi.service';

/** The type defs of this NgRx store. */
export interface MediaItemsState {
  idToDetails: ImmutableMap<string, Result<MediaItem>>;
}

/** The initial state of the NgRx store. */
export const buildInitialState: () => MediaItemsState = () => ({
  idToDetails: ImmutableMap(),
});

/** The feature key shared with the reducer. */
export const FEATURE_KEY = 'Media Items';

/** Returns the entire state of the media items store */
export const selectMediaItemsState =
  createFeatureSelector<MediaItemsState>(FEATURE_KEY);

/** Returns the media item details by id. */
export const selectMediaItemDetailsById = (id: string) =>
  createSelector(selectMediaItemsState, (state) =>
    state.idToDetails.get(id, toPending<MediaItem>()),
  );
