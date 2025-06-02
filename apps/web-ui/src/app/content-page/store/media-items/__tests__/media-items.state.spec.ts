import { Map as ImmutableMap } from 'immutable';

import {
  Result,
  toPending,
  toSuccess,
} from '../../../../shared/results/results';
import { MediaItem } from '../../../services/webapi.service';
import {
  buildInitialState,
  FEATURE_KEY,
  MediaItemsState,
  selectMediaItemDetailsById,
  selectMediaItemsState,
} from '../media-items.state'; // Adjust the import path as necessary

describe('Media Items Selectors', () => {
  it('should select the entire Media Items state', () => {
    const state: MediaItemsState = buildInitialState();

    const result = selectMediaItemsState.projector(state);

    expect(result).toEqual(state);
  });

  it('should return pending result when no media item exists', () => {
    const state: MediaItemsState = buildInitialState();

    const mediaItemId = 'nonExistingId';
    const result = selectMediaItemDetailsById(mediaItemId)({
      [FEATURE_KEY]: state,
    });

    expect(result).toEqual(toPending<MediaItem>());
  });

  it('should return media item details when it exists', () => {
    const mediaItemId = 'item123';
    const mediaItem: MediaItem = {
      id: 'item123',
      fileName: '',
      hashCode: '',
      gPhotosMediaItemId: '',
    };
    const state: MediaItemsState = {
      idToDetails: ImmutableMap<string, Result<MediaItem>>().set(
        mediaItemId,
        toSuccess(mediaItem),
      ),
    };

    const result = selectMediaItemDetailsById(mediaItemId)({
      [FEATURE_KEY]: state,
    });

    expect(result).toEqual(toSuccess(mediaItem));
  });

  it('should return pending for a media item that does not exist', () => {
    const mediaItemId = 'nonExistingId';
    const mediaItem: MediaItem = {
      id: 'existingId',
      fileName: '',
      hashCode: '',
      gPhotosMediaItemId: '',
    };
    const state: MediaItemsState = {
      idToDetails: ImmutableMap<string, Result<MediaItem>>().set(
        'existingId',
        toSuccess(mediaItem),
      ),
    };

    const result = selectMediaItemDetailsById(mediaItemId)({
      [FEATURE_KEY]: state,
    });

    expect(result).toEqual(toPending<MediaItem>());
  });
});
