import { toSuccess } from '../../../../shared/results/results';
import { Album, AlbumDetailsApiResponse } from '../../../services/types/album';
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

  it('should handle addAlbumResult', () => {
    const albumId = '123';
    const result = toSuccess<AlbumDetailsApiResponse>({
      id: albumId,
      albumName: 'Test Album',
      childAlbumIds: [],
      numChildAlbums: 0,
      numMediaItems: 0,
    });
    const action = albumsActions.addAlbumResult({
      albumId,
      result,
    });

    const initialState = buildInitialState();
    const newState = albumsReducer(initialState, action);

    expect(newState.idToDetails.get(albumId)).toEqual(result);
  });

  it('should handle addAlbum', () => {
    const albumId = '123';
    const album: Album = {
      id: albumId,
      albumName: 'Test Album',
      childAlbumIds: [],
      numChildAlbums: 0,
      numMediaItems: 0,
    };
    const action = albumsActions.addAlbum({ album });

    const initialState = buildInitialState();
    const newState = albumsReducer(initialState, action);

    expect(newState.idToDetails.get(albumId)).toEqual(
      toSuccess<AlbumDetailsApiResponse>(album),
    );
  });
});
