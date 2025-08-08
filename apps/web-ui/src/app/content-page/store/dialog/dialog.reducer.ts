import { createFeature, createReducer, on } from '@ngrx/store';

import { closeDialog, openDialog } from './dialog.actions';
import { DialogState, FEATURE_KEY, initialState } from './dialog.state';

export const dialogReducer = createReducer(
  initialState,

  on(openDialog, (state, { request }): DialogState => {
    return {
      ...state,
      request,
      isOpen: true,
    };
  }),

  on(closeDialog, (state): DialogState => {
    return {
      ...state,
      request: null,
      isOpen: false,
    };
  }),
);

export const dialogFeature = createFeature({
  name: FEATURE_KEY,
  reducer: dialogReducer,
});
