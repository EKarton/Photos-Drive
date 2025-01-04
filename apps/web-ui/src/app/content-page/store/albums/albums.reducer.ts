import { createFeature, createReducer, on } from '@ngrx/store';

import * as albumsActions from './albums.actions';
import { buildInitialState } from './albums.state';

/** The theme reducer */
export const albumsReducer = createReducer(
  buildInitialState(),

  on(albumsActions.loadAlbumDetailsResult, (state, { albumId, result }) => {
    return {
      ...state,
      idToDetails: state.idToDetails.set(albumId, result),
    };
  }),
);

export const albumsFeature = createFeature({
  name: 'Albums',
  reducer: albumsReducer,
});
