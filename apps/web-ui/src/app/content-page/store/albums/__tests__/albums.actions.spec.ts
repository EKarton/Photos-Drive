import { toSuccess } from '../../../../shared/results/results';
import { Album, AlbumDetailsApiResponse } from '../../../services/types/album';
import * as fromActions from '../albums.actions';

describe('Album Actions', () => {
  it('should create a loadAlbumDetails action', () => {
    const albumId = '123';
    const action = fromActions.loadAlbumDetails({ albumId });

    expect(action.type).toBe('[Albums] Load details of an album by ID');
    expect(action.albumId).toBe(albumId);
  });

  it('should create a loadAlbumDetailsResult action', () => {
    const albumId = '123';
    const result = toSuccess<AlbumDetailsApiResponse>({
      id: albumId,
      albumName: 'Test Album',
      parentAlbumId: undefined,
      childAlbumIds: [],
      numChildAlbums: 0,
      numMediaItems: 0,
    });
    const action = fromActions.addAlbumResult({ albumId, result });

    expect(action.type).toBe(
      '[Albums] Saves results of getting details of an album',
    );
    expect(action.albumId).toBe(albumId);
    expect(action.result).toEqual(result);
  });

  it('should create addAlbum action', () => {
    const album: Album = {
      id: '123',
      albumName: 'Test Album',
      parentAlbumId: undefined,
      childAlbumIds: [],
      numChildAlbums: 0,
      numMediaItems: 0,
    };
    const action = fromActions.addAlbum({ album });

    expect(action.type).toBe('[Albums] Add an album to the store');
    expect(action.album).toBe(album);
  });
});
