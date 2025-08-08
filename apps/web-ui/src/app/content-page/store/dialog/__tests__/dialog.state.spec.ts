import {
  initialState,
  DialogState,
  selectIsAnyDialogOpen,
  selectMediaItemsState,
  selectAnyDialogRequest,
} from '../dialog.state'; // Adjust the import path as necessary

describe('Media Viewer Selectors', () => {
  it('should select the entire Media Viewer state', () => {
    const result = selectMediaItemsState.projector(initialState);

    expect(result).toEqual(initialState);
  });

  it('should return null when there is no request', () => {
    const state: DialogState = initialState;

    const result = selectAnyDialogRequest().projector(state);

    expect(result).toBeNull();
  });

  it('should return the media viewer request when it exists', () => {
    const mediaItemId = 'item123';
    const state: DialogState = {
      ...initialState,
      request: { mediaItemId },
    };

    const result = selectAnyDialogRequest().projector(state);

    expect(result).toEqual({ mediaItemId });
  });

  it('should return false when isOpen is false', () => {
    const state: DialogState = initialState;

    const result = selectIsAnyDialogOpen().projector(state);

    expect(result).toBeFalse();
  });

  it('should return true when isOpen is true', () => {
    const state: DialogState = {
      ...initialState,
      isOpen: true,
    };

    const result = selectIsAnyDialogOpen().projector(state);

    expect(result).toBeTrue();
  });
});
