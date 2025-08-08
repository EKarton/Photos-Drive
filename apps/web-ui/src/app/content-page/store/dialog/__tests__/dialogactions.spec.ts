import { MediaViewerRequest } from '../../../media-viewer/media-viewer.request';
import { closeDialog, openDialog } from '../dialog.actions';

describe('Media Viewer Actions', () => {
  it('should create an action to open the media viewer', () => {
    const mediaItemId = 'item123';
    const request = new MediaViewerRequest(mediaItemId);

    const action = openDialog({ request });

    expect(action.type).toBe(
      '[Media Viwer] Requests the media viewer to be open with particular media item details',
    );
    expect(action.request).toEqual(request);
  });

  it('should create an action to close the media viewer', () => {
    const action = closeDialog();

    expect(action.type).toBe('[Media Viewer] Closes the media viewer');
  });
});
