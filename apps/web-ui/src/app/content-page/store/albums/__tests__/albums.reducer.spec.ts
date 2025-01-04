import { toSuccess } from '../../../../shared/results/results';
import { AlbumDetailsApiResponse } from '../../../services/webapi.service';
import * as albumsActions from '../albums.actions';
import { albumsReducer } from '../albums.reducer';
import { buildInitialState } from '../albums.state';

describe('Albums Reducer', () => {
  it('should return the initial state', () => {
    const action = { type: 'NOOP' };
    const initialState = buildInitialState();
    const result = albumsReducer(initialState, action);

    expect(result).toBe(initialState);
  });

  it('should handle loadAlbumDetails', () => {
    const albumId = '123';
    const action = albumsActions.loadAlbumDetails({ albumId });

    const initialState = buildInitialState();
    const result = albumsReducer(initialState, action);

    expect(result.idToDetails.get(albumId)).toBeUndefined();
  });

  it('should handle loadAlbumDetailsResult', () => {
    const albumId = '123';
    const result = toSuccess<AlbumDetailsApiResponse>({
      id: albumId,
      albumName: 'Test Album',
      childAlbumIds: [],
      mediaItemIds: [],
    });
    const action = albumsActions.loadAlbumDetailsResult({
      albumId,
      result,
    });

    const initialState = buildInitialState();
    const newState = albumsReducer(initialState, action);

    expect(newState.idToDetails.get(albumId)).toEqual(result);
  });
});
