import { createFeatureSelector, createSelector } from '@ngrx/store';

/** Represents a request to open a dialog. All dialog types must extend from this.  */
export type BaseDialogRequest = object;

/** The type defs of this NgRx store. */
export interface DialogState {
  request: BaseDialogRequest | null;
  isOpen: boolean;
}

/** The initial state of the NgRx store. */
export const initialState: DialogState = {
  request: null,
  isOpen: false,
};

/** The feature key shared with the reducer. */
export const FEATURE_KEY = 'Dialog';

/** Returns the entire state of the dialog store */
export const selectDialogState =
  createFeatureSelector<DialogState>(FEATURE_KEY);

/** Returns any request details of the dialog. */
export const selectAnyDialogRequest = () =>
  createSelector(selectDialogState, (state) => state.request);

/** Returns the request details for a particular dialog type */
export const selectDialogRequests = <T extends BaseDialogRequest>(
  ctor: new (...args: any[]) => T,
) =>
  createSelector(selectDialogState, (state) =>
    state.request instanceof ctor ? state.request : null,
  );

/** Returns whether any dialog is open or not. */
export const selectIsAnyDialogOpen = () =>
  createSelector(selectDialogState, (state) => state.isOpen);

export const selectIsDialogOpen = <T extends BaseDialogRequest>(
  ctor: new (...args: any[]) => T,
) =>
  createSelector(
    selectDialogState,
    (state) => state.isOpen && state.request instanceof ctor,
  );
