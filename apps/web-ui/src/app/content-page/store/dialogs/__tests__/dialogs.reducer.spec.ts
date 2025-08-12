import { MediaViewerRequest } from '../../../media-viewer/media-viewer.request';
import { closeDialog, openDialog } from '../dialogs.actions';
import { dialogReducer } from '../dialogs.reducer';
import { DialogState, initialState } from '../dialogs.state';

describe('Dialogs Reducer', () => {
  it('should handle openDialog action with a dialog request', () => {
    const request = new MediaViewerRequest('item123');

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
      request: new MediaViewerRequest('item123'),
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
