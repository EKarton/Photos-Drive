import { createFeature, createReducer, on } from '@ngrx/store';

import { closeMediaViewer, openMediaViewer } from './media-viewer.actions';
import {
  FEATURE_KEY,
  initialState,
  MediaViewerState,
} from './media-viewer.state';

export const mediaViewerReducer = createReducer(
  initialState,

  on(openMediaViewer, (state, { request }): MediaViewerState => {
    return {
      ...state,
      request,
      isOpen: true,
    };
  }),

  on(closeMediaViewer, (state): MediaViewerState => {
    return {
      ...state,
      request: null,
      isOpen: false,
    };
  }),
);

export const mediaViewerFeature = createFeature({
  name: FEATURE_KEY,
  reducer: mediaViewerReducer,
});
