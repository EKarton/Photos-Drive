import { toSuccess } from '../../../../shared/results/results';
import { MediaItem } from '../../../services/webapi.service';
import * as mediaItemsActions from '../media-items.actions';
import { mediaItemsReducer } from '../media-items.reducer';
import { buildInitialState } from '../media-items.state';

describe('Media Items Reducer', () => {
  it('should return the initial state', () => {
    const action = { type: 'NOOP' };

    const state = mediaItemsReducer(undefined, action);

    expect(state).toEqual(buildInitialState());
  });

  it('should handle loadMediaItemDetailsResult action', () => {
    const mediaItemId = 'item123';
    const mediaItem: MediaItem = {
      id: 'item123',
      fileName: '',
      hashCode: '',
      gPhotosClientId: '',
      gPhotosMediaItemId: '',
    };
    const mockResult = toSuccess(mediaItem);
    const action = mediaItemsActions.loadMediaItemDetailsResult({
      mediaItemId,
      result: mockResult,
    });

    const initialState = buildInitialState();
    const state = mediaItemsReducer(initialState, action);

    const expectedState = {
      ...initialState,
      idToDetails: initialState.idToDetails.set(mediaItemId, mockResult),
    };
    expect(state).toEqual(expectedState);
  });
});
