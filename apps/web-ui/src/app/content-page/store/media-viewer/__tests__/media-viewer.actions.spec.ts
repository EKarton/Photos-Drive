import { closeMediaViewer, openMediaViewer } from '../media-viewer.actions';
import { MediaViewerRequest } from '../media-viewer.state';

describe('Media Viewer Actions', () => {
  it('should create an action to open the media viewer', () => {
    const mediaItemId = 'item123';
    const request: MediaViewerRequest = { mediaItemId };

    const action = openMediaViewer({ request });

    expect(action.type).toBe(
      '[Media Viwer] Requests the media viewer to be open with particular media item details',
    );
    expect(action.request).toEqual(request);
  });

  it('should create an action to close the media viewer', () => {
    const action = closeMediaViewer();

    expect(action.type).toBe('[Media Viewer] Closes the media viewer');
  });
});
