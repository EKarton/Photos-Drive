import { Result, toSuccess } from '../../../../shared/results/results';
import { GPhotosMediaItemDetailsApiResponse } from '../../../services/webapi.service';
import {
  loadGPhotosMediaItemDetails,
  loadGPhotosMediaItemDetailsResult,
} from '../gphoto-media-items.actions';

describe('GPhotos Media Items Actions', () => {
  it('should create an action to load media item details', () => {
    const gPhotosMediaItemId = 'clientId:mediaItemId';

    const action = loadGPhotosMediaItemDetails({ gPhotosMediaItemId });

    expect(action.type).toBe(
      '[GPhotos Media Items] Load details of a media item from GPhotos by ID',
    );
    expect(action.gPhotosMediaItemId).toBe(gPhotosMediaItemId);
  });

  it('should create an action to save media item details result', () => {
    const gPhotosMediaItemId = 'client123:mediaItem123';
    const result: Result<GPhotosMediaItemDetailsApiResponse> = toSuccess({
      id: 'mediaItem123',
      baseUrl: '',
      mimeType: '',
      mediaMetadata: {
        creationTime: '',
        width: '0',
        height: '0',
      },
    });

    const action = loadGPhotosMediaItemDetailsResult({
      gPhotosMediaItemId,
      result,
    });

    expect(action.type).toBe(
      '[GPhotos Media Items] Saves results of getting details of a media item from GPhotos',
    );
    expect(action.gPhotosMediaItemId).toBe(gPhotosMediaItemId);
    expect(action.result).toBe(result);
  });
});
