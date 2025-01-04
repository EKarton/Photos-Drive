import { createFeatureSelector, createSelector } from '@ngrx/store';

/** Represents the request for opening the image viewer. */
export interface MediaViewerRequest {
  mediaItemId: string;
}

/** The type defs of this NgRx store. */
export interface MediaViewerState {
  request: MediaViewerRequest | null;
  isOpen: boolean;
}

/** The initial state of the NgRx store. */
export const initialState: MediaViewerState = {
  request: null,
  isOpen: false,
};

/** The feature key shared with the reducer. */
export const FEATURE_KEY = 'Media Viewer';

/** Returns the entire state of the media items store */
export const selectMediaItemsState =
  createFeatureSelector<MediaViewerState>(FEATURE_KEY);

/** Returns the request details of the image. */
export const selectRequest = () =>
  createSelector(selectMediaItemsState, (state) => state.request);

/** Returns whether the dialog is open or not. */
export const selectIsOpen = () =>
  createSelector(selectMediaItemsState, (state) => state.isOpen);
