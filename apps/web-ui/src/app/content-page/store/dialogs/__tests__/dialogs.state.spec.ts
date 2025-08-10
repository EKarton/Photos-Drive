import { ChatDialogRequest } from '../../../chat-dialog/chat-dialog.request';
import { MediaViewerRequest } from '../../../media-viewer/media-viewer.request';
import {
  DialogState,
  initialState,
  selectAnyDialogRequest,
  selectDialogRequests,
  selectDialogState,
  selectIsAnyDialogOpen,
  selectIsDialogOpen,
} from '../dialogs.state';

describe('Dialogs Selectors', () => {
  it('should select the entire Dialog state', () => {
    const result = selectDialogState.projector({ ...initialState });

    expect(result).toEqual(initialState);
  });

  describe('selectAnyDialogRequest', () => {
    it('should return null when there is no request', () => {
      const state: DialogState = { ...initialState, request: null };

      const result = selectAnyDialogRequest().projector(state);

      expect(result).toBeNull();
    });

    it('should return the dialog request when it exists', () => {
      const request = new MediaViewerRequest('item123');
      const state: DialogState = {
        ...initialState,
        request,
      };

      const result = selectAnyDialogRequest().projector(state);

      expect(result).toEqual(request);
    });
  });

  describe('selectDialogRequests', () => {
    it('should return the request when it is an instance of the given ctor', () => {
      const request = new MediaViewerRequest('item123');
      const state: DialogState = {
        request,
        isOpen: true,
      };

      const selector = selectDialogRequests(MediaViewerRequest);
      const result = selector.projector(state);

      expect(result).toBe(request);
    });

    it('should return null when the request is not an instance of the given ctor', () => {
      const request = new ChatDialogRequest();
      const state: DialogState = {
        request,
        isOpen: true,
      };

      const selector = selectDialogRequests(MediaViewerRequest);
      const result = selector.projector(state);

      expect(result).toBeNull();
    });

    it('should return null when request is null', () => {
      const state: DialogState = {
        request: null,
        isOpen: false,
      };

      const selector = selectDialogRequests(MediaViewerRequest);
      const result = selector.projector(state);

      expect(result).toBeNull();
    });
  });

  describe('selectIsAnyDialogOpen', () => {
    it('should return false when isOpen is false', () => {
      const state: DialogState = { ...initialState, isOpen: false };

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

  describe('selectIsDialogOpen', () => {
    it('should return true if isOpen is true and request is instance of the given ctor', () => {
      const request = new MediaViewerRequest('item123');
      const state: DialogState = {
        request,
        isOpen: true,
      };

      const selector = selectIsDialogOpen(MediaViewerRequest);
      const result = selector.projector(state);

      expect(result).toBeTrue();
    });

    it('should return false if isOpen is false even if request is instance of the given ctor', () => {
      const request = new MediaViewerRequest('item123');
      const state: DialogState = {
        request,
        isOpen: false,
      };

      const selector = selectIsDialogOpen(MediaViewerRequest);
      const result = selector.projector(state);

      expect(result).toBeFalse();
    });

    it('should return false if request is not instance of the given ctor even if isOpen is true', () => {
      const request = new ChatDialogRequest();
      const state: DialogState = {
        request,
        isOpen: true,
      };

      const selector = selectIsDialogOpen(MediaViewerRequest);
      const result = selector.projector(state);

      expect(result).toBeFalse();
    });

    it('should return false if request is null and isOpen is true', () => {
      const state: DialogState = {
        request: null,
        isOpen: true,
      };

      const selector = selectIsDialogOpen(MediaViewerRequest);
      const result = selector.projector(state);

      expect(result).toBeFalse();
    });
  });
});
