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
  MediaItemsRepository
} from '../../src/services/metadata_store/MediaItemsRepository';
import { MongoDbClientNotFoundError } from '../../src/services/metadata_store/MongoDbClientsRepository';
import { fakeAuthEnv, generateTestToken } from './utils/auth';
import { setupTestEnv } from './utils/env';

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
