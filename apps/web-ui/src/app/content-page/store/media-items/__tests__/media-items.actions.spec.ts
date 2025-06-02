import { toSuccess } from '../../../../shared/results/results';
import { MediaItemDetailsApiResponse } from '../../../services/webapi.service';
import {
  loadMediaItemDetails,
  loadMediaItemDetailsResult,
} from '../media-items.actions';

describe('Media Item Actions', () => {
  it('should create an action to load media item details', () => {
    const mediaItemId = 'item123';

    const action = loadMediaItemDetails({ mediaItemId });

    expect(action.type).toBe(
      '[Media Items] Load details of a media item by ID',
    );
    expect(action.mediaItemId).toBe(mediaItemId);
  });

  it('should create an action to save media item details result', () => {
    const mediaItemId = 'item123';
    const mediaItem: MediaItemDetailsApiResponse = {
      id: mediaItemId,
      fileName: '',
      hashCode: '',
      gPhotosMediaItemId: '',
    };

    const action = loadMediaItemDetailsResult({
      mediaItemId,
      result: toSuccess(mediaItem),
    });

    expect(action.type).toBe(
      '[Media Items] Saves results of getting details of a media item',
    );
    expect(action.mediaItemId).toBe(mediaItemId);
    expect(action.result).toEqual(toSuccess(mediaItem));
  });
});
