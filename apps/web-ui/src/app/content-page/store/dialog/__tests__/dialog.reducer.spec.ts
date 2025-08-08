import { closeDialog, openDialog } from '../dialog.actions';
import { dialogReducer } from '../dialog.reducer';
import { DialogState, initialState } from '../dialog.state';

describe('Media Viewer Reducer', () => {
  it('should return the initial state', () => {
    const action = { type: 'NOOP' };

    const state = dialogReducer(undefined, action);

    expect(state).toEqual(initialState);
  });

  it('should handle openDialog action', () => {
    const mediaItemId = 'item123';
    const request = { mediaItemId };

    const action = openDialog({ request });
    const state = dialogReducer(initialState, action);

    const expectedState: DialogState = {
      ...initialState,
      request,
      isOpen: true,
    };
    expect(state).toEqual(expectedState);
  });

  it('should handle closeDialog action', () => {
    const initialStateWithRequest: DialogState = {
      ...initialState,
      request: { mediaItemId: 'item123' }, // Set a mock request
      isOpen: true,
    };

    const action = closeDialog();
    const state = dialogReducer(initialStateWithRequest, action);

    const expectedState: DialogState = {
      ...initialStateWithRequest,
      request: null,
      isOpen: false,
    };
    expect(state).toEqual(expectedState);
  });
});
