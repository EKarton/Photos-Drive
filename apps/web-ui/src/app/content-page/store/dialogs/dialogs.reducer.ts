import { createFeature, createReducer, on } from '@ngrx/store';

import { closeDialog, openDialog } from './dialogs.actions';
import { DialogState, FEATURE_KEY, initialState } from './dialogs.state';

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
