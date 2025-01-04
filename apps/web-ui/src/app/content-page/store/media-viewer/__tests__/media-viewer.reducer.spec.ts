import { closeMediaViewer, openMediaViewer } from '../media-viewer.actions';
import { mediaViewerReducer } from '../media-viewer.reducer';
import { initialState, MediaViewerState } from '../media-viewer.state';

describe('Media Viewer Reducer', () => {
  it('should return the initial state', () => {
    const action = { type: 'NOOP' };

    const state = mediaViewerReducer(undefined, action);

    expect(state).toEqual(initialState);
  });

  it('should handle openMediaViewer action', () => {
    const mediaItemId = 'item123';
    const request = { mediaItemId };

    const action = openMediaViewer({ request });
    const state = mediaViewerReducer(initialState, action);

    const expectedState: MediaViewerState = {
      ...initialState,
      request,
      isOpen: true,
    };
    expect(state).toEqual(expectedState);
  });

  it('should handle closeMediaViewer action', () => {
    const initialStateWithRequest: MediaViewerState = {
      ...initialState,
      request: { mediaItemId: 'item123' }, // Set a mock request
      isOpen: true,
    };

    const action = closeMediaViewer();
    const state = mediaViewerReducer(initialStateWithRequest, action);

    const expectedState: MediaViewerState = {
      ...initialStateWithRequest,
      request: null,
      isOpen: false,
    };
    expect(state).toEqual(expectedState);
  });
});
