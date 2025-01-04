import { createFeatureSelector, createSelector } from '@ngrx/store';
import { Map as ImmutableMap } from 'immutable';

import { Result, toPending } from '../../../shared/results/results';
import { mapResultt } from '../../../shared/results/utils/mapResultt';

/** The type defs of this NgRx store. */
export interface GPhotoClientsState {
  idToClientResult: Result<ImmutableMap<string, Result<string>>>;
}

/** The initial state of the NgRx store. */
export const initialState: GPhotoClientsState = {
  idToClientResult: toPending(),
};

/** The feature key shared with the reducer. */
export const FEATURE_KEY = 'GPhotoClients';

/** Returns the entire state of the GPhotoClients store */
export const selectGPhotosClientsState =
  createFeatureSelector<GPhotoClientsState>(FEATURE_KEY);

/** Returns the token of a GPhotoClient. */
export const selectToken = (id: string) =>
  createSelector(selectGPhotosClientsState, (state) => {
    return mapResultt(state.idToClientResult, (idToClient) => {
      return idToClient.get(id, toPending<string>());
    });
  });
