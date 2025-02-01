import { Result, toSuccess } from '../../../../shared/results/results';
import { GPhotosMediaItem } from '../../../services/webapi.service';
import {
  loadGPhotosMediaItemDetails,
  loadGPhotosMediaItemDetailsResult,
} from '../gphoto-media-items.actions';

describe('GPhotos Media Items Actions', () => {
  it('should create an action to load media item details', () => {
    const gMediaItemId = 'clientId:mediaItemId';

    const action = loadGPhotosMediaItemDetails({ gMediaItemId });

    expect(action.type).toBe(
      '[GPhotos Media Items] Load details of a media item from GPhotos by ID',
    );
    expect(action.gMediaItemId).toBe(gMediaItemId);
  });

  it('should create an action to save media item details result', () => {
    const gMediaItemId = 'client123:mediaItem123';
    const result: Result<GPhotosMediaItem> = toSuccess({
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
      gMediaItemId,
      result,
    });

    expect(action.type).toBe(
      '[GPhotos Media Items] Saves results of getting details of a media item from GPhotos',
    );
    expect(action.gMediaItemId).toBe(gMediaItemId);
    expect(action.result).toBe(result);
  });
});
