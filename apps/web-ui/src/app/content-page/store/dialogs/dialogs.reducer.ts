import { createFeature, createReducer, on } from '@ngrx/store';

import { closeDialog, openDialog } from './dialogs.actions';
import { DialogState, FEATURE_KEY, initialState } from './dialogs.state';

export const dialogReducer = createReducer(
  initialState,

  on(openDialog, (_state, { request }): DialogState => {
    return {
      request,
      isOpen: true,
    };
  }),

  on(closeDialog, (): DialogState => {
    return {
      request: null,
      isOpen: false,
    };
  }),
);

export const dialogFeature = createFeature({
  name: FEATURE_KEY,
  reducer: dialogReducer,
});
