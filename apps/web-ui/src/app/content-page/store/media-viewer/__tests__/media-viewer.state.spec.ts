import {
  initialState,
  MediaViewerState,
  selectIsOpen,
  selectMediaItemsState,
  selectRequest,
} from '../media-viewer.state'; // Adjust the import path as necessary

describe('Media Viewer Selectors', () => {
  it('should select the entire Media Viewer state', () => {
    const result = selectMediaItemsState.projector(initialState);

    expect(result).toEqual(initialState);
  });

  it('should return null when there is no request', () => {
    const state: MediaViewerState = initialState;

    const result = selectRequest().projector(state);

    expect(result).toBeNull();
  });

  it('should return the media viewer request when it exists', () => {
    const mediaItemId = 'item123';
    const state: MediaViewerState = {
      ...initialState,
      request: { mediaItemId },
    };

    const result = selectRequest().projector(state);

    expect(result).toEqual({ mediaItemId });
  });

  it('should return false when isOpen is false', () => {
    const state: MediaViewerState = initialState;

    const result = selectIsOpen().projector(state);

    expect(result).toBeFalse();
  });

  it('should return true when isOpen is true', () => {
    const state: MediaViewerState = {
      ...initialState,
      isOpen: true,
    };

    const result = selectIsOpen().projector(state);

    expect(result).toBeTrue();
  });
});
