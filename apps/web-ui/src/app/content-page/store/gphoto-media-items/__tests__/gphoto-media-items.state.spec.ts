import { Map as ImmutableMap } from 'immutable';

import {
  Result,
  toPending,
  toSuccess,
} from '../../../../shared/results/results';
import { GPhotosMediaItemApiResponse } from '../../../services/gphotos-api.service';
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
    const mediaItemResult: Result<GPhotosMediaItemApiResponse> = toSuccess({
      id: 'mediaItemId',
      description: '',
      productUrl: '',
      baseUrl: '',
      mimeType: '',
      mediaMetadata: {
        creationTime: '',
        width: 0,
        height: 0,
      },
      contributorInfo: {
        profilePictureBaseUrl: '',
        displayName: '',
      },
      filename: '',
    });
    const initialState: GPhotosMediaItemsState = {
      idToDetails: ImmutableMap<
        string,
        Result<GPhotosMediaItemApiResponse>
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

    expect(result).toEqual(toPending<GPhotosMediaItemApiResponse>());
  });
});
