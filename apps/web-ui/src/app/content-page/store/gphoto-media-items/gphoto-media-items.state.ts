import { createFeatureSelector, createSelector } from '@ngrx/store';
import { Map as ImmutableMap } from 'immutable';

import { Result, toPending } from '../../../shared/results/results';
import { GPhotosMediaItem } from '../../services/webapi.service';

/** The type defs of this NgRx store. */
export interface GPhotosMediaItemsState {
  idToDetails: ImmutableMap<string, Result<GPhotosMediaItem>>;
}

/** The initial state of the NgRx store. */
export const buildInitialState: () => GPhotosMediaItemsState = () => ({
  idToDetails: ImmutableMap(),
});

/** The feature key shared with the reducer. */
export const FEATURE_KEY = 'GPhotosMediaItems';

/** Returns the entire state of the media items store */
export const selectGPhotosMediaItemsState =
  createFeatureSelector<GPhotosMediaItemsState>(FEATURE_KEY);

/** Returns the GPhotos media item details by id. */
export const selectGPhotosMediaItemById = (id: string) =>
  createSelector(selectGPhotosMediaItemsState, (state) =>
    state.idToDetails.get(id, toPending<GPhotosMediaItem>()),
  );
