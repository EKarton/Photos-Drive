import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import searchMediaItemsRouter from '../../../src/routes/media_items/search_media_items';
import {
  MediaItemsStore,
  SortByDirection,
  SortByField
} from '../../../src/services/core/media_items/BaseMediaItemsStore';
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

describe('GET api/v1/media-items/search', () => {
  let cleanupTestEnvFn = () => { };
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

  it('should return 200 with default params when query params are missing', async () => {
    const repo = mock<MediaItemsStore>();
    repo.listMediaItems.mockResolvedValue({
      mediaItems: MOCK_MEDIA_ITEMS,
      nextPageToken: undefined
    });
    const app = express();
    app.use(await searchMediaItemsRouter(repo));

    const res = await request(app)
      .get('/api/v1/media-items/search')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(200);
    expect(res.body).toEqual({
      mediaItems: [
        {
          id: 'albumClient1:mediaItem1',
          albumId: 'albumClient1:albumObject1',
          fileName: 'dog.png',
          gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
          location: {
            latitude: 123,
            longitude: 456
          },
          width: 1000,
          height: 2000,
          dateTaken: '2025-06-07T17:00:00.000Z'
        },
        {
          id: 'albumClient1:mediaItem2',
          albumId: 'albumClient1:albumObject1',
          fileName: 'cat.png',
          gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
          location: {
            latitude: 123,
            longitude: 456
          },
          width: 100,
          height: 200,
          dateTaken: '2024-06-07T17:00:00.000Z'
        }
      ],
      nextPageToken: undefined
    });
    expect(repo.listMediaItems).toHaveBeenCalledWith(
      {
        pageSize: 25,
        pageToken: undefined,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      },
      { abortController: expect.any(AbortController) }
    );
  });

  it('should return 200 with query params populated', async () => {
    const repo = mock<MediaItemsStore>();
    repo.listMediaItems.mockResolvedValue({
      mediaItems: [],
      nextPageToken: 'next-token'
    });

    const app = express();
    app.use(await searchMediaItemsRouter(repo));

    const res = await request(app)
      .get(
        '/api/v1/media-items/search?albumId=albumClient1:albumObject1&pageSize=10&pageToken=abc&sortBy=id&sortDir=asc&earliest=2025-01-01T00:00:00Z&latest=2025-04-01T00:00:00Z&latitude=-48&longitude=95&range=300'
      )
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(200);
    expect(res.body).toEqual({
      mediaItems: [],
      nextPageToken: 'next-token'
    });
    expect(repo.listMediaItems).toHaveBeenCalledWith(
      {
        albumId: {
          clientId: 'albumClient1',
          objectId: 'albumObject1'
        },
        earliestDateTaken: new Date('2025-01-01T00:00:00Z'),
        latestDateTaken: new Date('2025-04-01T00:00:00Z'),
        withinLocation: {
          latitude: -48,
          longitude: 95,
          range: 300
        },
        pageSize: 10,
        pageToken: 'abc',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      },
      { abortController: expect.any(AbortController) }
    );
  });

  it('should return 400 when request is not valid', async () => {
    const repo = mock<MediaItemsStore>();
    repo.listMediaItems.mockResolvedValue({
      mediaItems: [],
      nextPageToken: 'next-token'
    });

    const app = express();
    app.use(await searchMediaItemsRouter(repo));

    const res = await request(app)
      .get('/api/v1/media-items/search?pageSize=1000')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'Invalid request' });
  });

  it('should return 500 when an unexpected error is thrown', async () => {
    const repo = mock<MediaItemsStore>();
    repo.listMediaItems.mockRejectedValue(new Error('Something went wrong'));
    const app = express();
    app.use(await searchMediaItemsRouter(repo));

    const res = await request(app)
      .get('/api/v1/media-items/search')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(500);
  });
});
