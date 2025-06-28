import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import mediaItemsRouter from '../../src/routes/media_items';
import {
  MediaItem,
  MediaItemId
} from '../../src/services/metadata_store/MediaItems';
import {
  MediaItemNotFoundError,
  MediaItemsRepository,
  SortByDirection,
  SortByField
} from '../../src/services/metadata_store/MediaItemsRepository';
import { MongoDbClientNotFoundError } from '../../src/services/metadata_store/mongodb/MongoDbClientsRepository';
import { fakeAuthEnv, generateTestToken } from './utils/auth';
import { setupTestEnv } from './utils/env';

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

describe('Media Items Router', () => {
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

  describe('GET api/v1/media-items', () => {
    it('should return 200 with default pageSize and no sort when query params are missing', async () => {
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockMediaItemsRepository.listMediaItems.mockResolvedValue({
        mediaItems: MOCK_MEDIA_ITEMS,
        nextPageToken: undefined
      });

      const app = express();
      app.use(await mediaItemsRouter(mockMediaItemsRepository));

      const res = await request(app)
        .get('/api/v1/media-items')
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
      expect(mockMediaItemsRepository.listMediaItems).toHaveBeenCalledWith({
        pageSize: 25,
        pageToken: undefined,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });
    });

    it('should return 200 with albumId', async () => {
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockMediaItemsRepository.listMediaItems.mockResolvedValue({
        mediaItems: [],
        nextPageToken: 'next-token'
      });

      const app = express();
      app.use(await mediaItemsRouter(mockMediaItemsRepository));

      const res = await request(app)
        .get('/api/v1/media-items?albumId=albumClient1:albumObject1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toEqual({
        mediaItems: [],
        nextPageToken: 'next-token'
      });
      expect(mockMediaItemsRepository.listMediaItems).toHaveBeenCalledWith({
        albumId: {
          clientId: 'albumClient1',
          objectId: 'albumObject1'
        },
        pageSize: 25,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });
    });

    it('should return 200 with pageToken, sortBy=id, and sortDir=asc', async () => {
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockMediaItemsRepository.listMediaItems.mockResolvedValue({
        mediaItems: [],
        nextPageToken: 'next-token'
      });

      const app = express();
      app.use(await mediaItemsRouter(mockMediaItemsRepository));

      const res = await request(app)
        .get(
          '/api/v1/media-items?pageSize=10&pageToken=abc&sortBy=id&sortDir=asc'
        )
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toEqual({
        mediaItems: [],
        nextPageToken: 'next-token'
      });
      expect(mockMediaItemsRepository.listMediaItems).toHaveBeenCalledWith({
        pageSize: 10,
        pageToken: 'abc',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });
    });

    it('should return 200 with pageToken, sortBy=id, and sortDir=desc', async () => {
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockMediaItemsRepository.listMediaItems.mockResolvedValue({
        mediaItems: [],
        nextPageToken: 'next-token'
      });

      const app = express();
      app.use(await mediaItemsRouter(mockMediaItemsRepository));

      const res = await request(app)
        .get(
          '/api/v1/media-items?pageSize=10&pageToken=abc&sortBy=id&sortDir=desc'
        )
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toEqual({
        mediaItems: [],
        nextPageToken: 'next-token'
      });
      expect(mockMediaItemsRepository.listMediaItems).toHaveBeenCalledWith({
        pageSize: 10,
        pageToken: 'abc',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.DESCENDING
        }
      });
    });

    it('should return 500 when an unexpected error is thrown', async () => {
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockMediaItemsRepository.listMediaItems.mockRejectedValue(
        new Error('Something went wrong')
      );

      const app = express();
      app.use(await mediaItemsRouter(mockMediaItemsRepository));

      const res = await request(app)
        .get('/api/v1/media-items')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(500);
    });
  });

  describe('GET /api/v1/media-items/:id', () => {
    it('should return 200 response with correct body given valid media item id', async () => {
      const mockMediaItem: MediaItem = {
        id: {
          clientId: 'mediaItemClientId1',
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
          clientId: '407f1f77bcf86cd799439001',
          objectId: '407f1f77bcf86cd799439002'
        },
        width: 1000,
        height: 2000,
        date_taken: new Date('2025-06-07T17:00:00.000Z')
      };
      const repo = mock<MediaItemsRepository>();
      repo.getMediaItemById.mockResolvedValue(mockMediaItem);
      const app = express();
      app.use(await mediaItemsRouter(repo));

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body).toEqual({
        id: 'mediaItemClientId1:mediaItem1',
        fileName: 'dog.png',
        location: {
          latitude: 123,
          longitude: 456
        },
        gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
        albumId: '407f1f77bcf86cd799439001:407f1f77bcf86cd799439002',
        width: 1000,
        height: 2000,
        dateTaken: '2025-06-07T17:00:00.000Z'
      });
    });

    it('should return 404 response given MediaItemsRepository returns MongoDbClientNotFoundError', async () => {
      const repo = mock<MediaItemsRepository>();
      repo.getMediaItemById.mockRejectedValue(
        new MongoDbClientNotFoundError('mediaItemClientId1:mediaItem1')
      );
      const app = express();
      app.use(await mediaItemsRouter(repo));

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(404);
      expect(res.body).toEqual({ error: 'Media item not found' });
    });

    it('should return 404 response given MediaItemsRepository returns MediaItemNotFoundError', async () => {
      const mediaItemId: MediaItemId = {
        clientId: 'mediaItemClientId1',
        objectId: 'mediaItem1'
      };
      const repo = mock<MediaItemsRepository>();
      repo.getMediaItemById.mockRejectedValue(
        new MediaItemNotFoundError(mediaItemId)
      );
      const app = express();
      app.use(await mediaItemsRouter(repo));

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(404);
      expect(res.body).toEqual({ error: 'Media item not found' });
    });

    it('should return 500 response given MediaItemsRepository returns random error', async () => {
      const repo = mock<MediaItemsRepository>();
      repo.getMediaItemById.mockRejectedValue(new Error('Random error'));
      const app = express();
      app.use(await mediaItemsRouter(repo));

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(500);
      expect(res.body).toEqual({});
    });
  });
});
