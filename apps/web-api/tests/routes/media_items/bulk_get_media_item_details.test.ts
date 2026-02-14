import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import bulkGetMediaItemDetails from '../../../src/routes/media_items/bulk_get_media_item_details';
import { MediaItemsStore } from '../../../src/services/core/media_items/BaseMediaItemsStore';
import { MediaItem } from '../../../src/services/core/media_items/MediaItems';
import { fakeAuthEnv, generateTestToken } from '../utils/auth';
import { setupTestEnv } from '../utils/env';

const MOCK_MEDIA_ITEMS: MediaItem[] = [
  {
    id: {
      clientId: 'albumClient1',
      objectId: 'mediaItem1'
    },
    file_name: 'dog.png',
    location: {
      latitude: 123,
      longitude: 456
    },
    gphotos_client_id: 'gPhotosClient1',
    gphotos_media_item_id: 'gPhotosMediaItem1',
    album_id: {
      clientId: 'albumClient1',
      objectId: 'albumObject1'
    },
    width: 1000,
    height: 2000,
    date_taken: new Date('2025-06-07T17:00:00.000Z')
  },
  {
    id: {
      clientId: 'albumClient1',
      objectId: 'mediaItem2'
    },
    file_name: 'cat.png',
    location: {
      latitude: 123,
      longitude: 456
    },
    gphotos_client_id: 'gPhotosClient1',
    gphotos_media_item_id: 'gPhotosMediaItem1',
    album_id: {
      clientId: 'albumClient1',
      objectId: 'albumObject1'
    },
    width: 100,
    height: 200,
    date_taken: new Date('2024-06-07T17:00:00.000Z')
  }
];

describe('POST /api/v1/media-items/bulk-get', () => {
  let cleanupTestEnvFn = () => {};
  let token = '';

  beforeEach(async () => {
    jest.resetModules();
    cleanupTestEnvFn = setupTestEnv({
      ...fakeAuthEnv
    });
    token = await generateTestToken();
  });

  afterEach(() => {
    cleanupTestEnvFn();
  });

  it('should return 200 with media items', async () => {
    const repo = mock<MediaItemsStore>();
    repo.bulkGetMediaItemByIds.mockResolvedValue(MOCK_MEDIA_ITEMS);
    const app = express();
    app.use(express.json());
    app.use(await bulkGetMediaItemDetails(repo));

    const res = await request(app)
      .post('/api/v1/media-items/bulk-get')
      .set('Authorization', `Bearer ${token}`)
      .send({
        mediaItemIds: ['albumClient1:mediaItem1', 'albumClient1:mediaItem2']
      });

    expect(res.statusCode).toBe(200);
    expect(res.body).toEqual({
      mediaItems: [
        {
          id: 'albumClient1:mediaItem1',
          fileName: 'dog.png',
          location: { latitude: 123, longitude: 456 },
          gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
          albumId: 'albumClient1:albumObject1',
          width: 1000,
          height: 2000,
          dateTaken: '2025-06-07T17:00:00.000Z'
        },
        {
          id: 'albumClient1:mediaItem2',
          fileName: 'cat.png',
          location: { latitude: 123, longitude: 456 },
          gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
          albumId: 'albumClient1:albumObject1',
          width: 100,
          height: 200,
          dateTaken: '2024-06-07T17:00:00.000Z'
        }
      ]
    });
  });

  it('should return 400 if there are too many media items to request for', async () => {
    const repo = mock<MediaItemsStore>();
    const app = express();
    app.use(express.json());
    app.use(await bulkGetMediaItemDetails(repo));

    const tooManyIds = new Array(51).fill('albumClient1:mediaItem1');

    const res = await request(app)
      .post('/api/v1/media-items/bulk-get')
      .set('Authorization', `Bearer ${token}`)
      .send({
        mediaItemIds: tooManyIds
      });

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({
      error:
        'Invalid request body, mediaItemIds must be string array with at most 50 items'
    });
    expect(repo.bulkGetMediaItemByIds).not.toHaveBeenCalled();
  });

  it('should return 500 if there is an error with fetching media items', async () => {
    const repo = mock<MediaItemsStore>();
    repo.bulkGetMediaItemByIds.mockRejectedValue(new Error('Database failure'));
    const app = express();
    app.use(express.json());
    app.use(await bulkGetMediaItemDetails(repo));

    const res = await request(app)
      .post('/api/v1/media-items/bulk-get')
      .set('Authorization', `Bearer ${token}`)
      .send({
        mediaItemIds: ['albumClient1:mediaItem1']
      });

    expect(res.statusCode).toBe(500);
  });
});
