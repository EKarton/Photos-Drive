import { createFeature, createReducer, on } from '@ngrx/store';
import { Map as ImmutableMap } from 'immutable';

import { toSuccess } from '../../../shared/results/results';
import { combineResults2 } from '../../../shared/results/utils/combineResults2';
import { mapResult } from '../../../shared/results/utils/mapResult';
import * as gphotoClientsActions from './gphotos-clients.actions';
import {
  FEATURE_KEY,
  GPhotoClientsState,
  initialState,
} from './gphotos-clients.state';

export const gphotosClientsReducer = createReducer(
  initialState,

  on(
    gphotoClientsActions.loadGPhotoClientsResults,
    (state, { result }): GPhotoClientsState => {
      return {
        ...state,
        idToClientResult: mapResult(result, (data) => {
          return ImmutableMap(
            data.gphotoClients.map((item) => [item.id, toSuccess(item.token)]),
          );
        }),
      };
    },
  ),

  on(
    gphotoClientsActions.loadRefreshTokenResult,
    (state, { clientId, result }): GPhotoClientsState => {
      return {
        ...state,
        idToClientResult: combineResults2(
          state.idToClientResult,
          result,
          (idToClient, res) => {
            return idToClient.set(clientId, toSuccess(res.newToken));
          },
        ),
      };
    },
  ),
);

export const gPhotosClientsFeature = createFeature({
  name: FEATURE_KEY,
  reducer: gphotosClientsReducer,
});
