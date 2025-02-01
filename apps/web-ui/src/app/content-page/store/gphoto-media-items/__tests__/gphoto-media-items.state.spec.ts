import { Map as ImmutableMap } from 'immutable';

import {
  Result,
  toPending,
  toSuccess,
} from '../../../../shared/results/results';
import { GPhotosMediaItemDetailsApiResponse } from '../../../services/webapi.service';
import {
  GPhotosMediaItemsState,
  selectGPhotosMediaItemById,
  selectGPhotosMediaItemsState,
} from '../gphoto-media-items.state';
import { buildInitialState } from '../gphoto-media-items.state';

describe('GPhoto Media Items Selectors', () => {
  it('should select the GPhoto Media Items state', () => {
    const initialState = buildInitialState();

    const result = selectGPhotosMediaItemsState.projector(initialState);

    expect(result).toEqual(initialState);
  });

  it('should select a media item by ID', () => {
    const gPhotosMediaItemId = 'clientId:mediaItemId';
    const mediaItemResult: Result<GPhotosMediaItemDetailsApiResponse> =
      toSuccess({
        baseUrl: '',
        mimeType: '',
        mediaMetadata: {
          creationTime: '',
          width: '0',
          height: '0',
        },
      });
    const initialState: GPhotosMediaItemsState = {
      idToDetails: ImmutableMap<
        string,
        Result<GPhotosMediaItemDetailsApiResponse>
      >().set(gPhotosMediaItemId, mediaItemResult),
    };

    const result = selectGPhotosMediaItemById(gPhotosMediaItemId)({
      GPhotosMediaItems: initialState,
    });

    expect(result).toEqual(mediaItemResult);
  });

  it('should return pending state for non-existing media item', () => {
    const nonExistingId = 'nonExistingId';

    const result = selectGPhotosMediaItemById(nonExistingId)({
      GPhotosMediaItems: buildInitialState(),
    });

    expect(result).toEqual(toPending<GPhotosMediaItemDetailsApiResponse>());
  });
});
