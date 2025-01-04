import { createAction, props } from '@ngrx/store';

import { MediaViewerRequest } from './media-viewer.state';

/** An action that requests for the dialog to be open. */
export const openMediaViewer = createAction(
  '[Media Viwer] Requests the media viewer to be open with particular media item details',
  props<{ request: MediaViewerRequest }>(),
);

/** An action that closes the media viewer. */
export const closeMediaViewer = createAction(
  '[Media Viewer] Closes the media viewer',
);
