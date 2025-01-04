import { Result, toSuccess } from '../../../../shared/results/results';
import { GPhotosMediaItemDetails } from '../../../services/gphotos-api.service';
import * as gPhotosMediaItemsActions from '../gphoto-media-items.actions';
import { gPhotosMediaItemsReducer } from '../gphoto-media-items.reducer';
import { buildInitialState } from '../gphoto-media-items.state';

describe('GPhotos Media Items Reducer', () => {
  it('should return the initial state', () => {
    const action = { type: 'NOOP' };

    const initialState = buildInitialState();
    const state = gPhotosMediaItemsReducer(initialState, action);

    expect(state).toEqual(initialState);
  });

  it('should handle loadGPhotosMediaItemDetailsResult action', () => {
    const initialState = buildInitialState();
    const gPhotosMediaItemId = 'clientId:mediaItemId';
    const result: Result<GPhotosMediaItemDetails> = toSuccess({
      id: 'mediaItemId',
      description: '',
      productUrl: '',
      baseUrl: '',
      mimeType: '',
      mediaMetadata: {
        creationTime: '',
        width: 0,
        height: 0,
      },
      contributorInfo: {
        profilePictureBaseUrl: '',
        displayName: '',
      },
      filename: '',
    });

    const action = gPhotosMediaItemsActions.loadGPhotosMediaItemDetailsResult({
      gPhotosMediaItemId,
      result,
    });
    const state = gPhotosMediaItemsReducer(initialState, action);

    expect(state.idToDetails.get(gPhotosMediaItemId)).toEqual(result);
  });
});
