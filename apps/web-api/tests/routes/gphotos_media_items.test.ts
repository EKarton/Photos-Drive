import { AxiosError } from 'axios';
import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import gPhotosMediaItemsRouter from '../../src/routes/gphotos_media_items';
import { GPhotosClient } from '../../src/services/core/storage/gphotos/GPhotosClient';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../../src/services/core/storage/gphotos/GPhotosClientsRepository';
import { fakeAuthEnv, generateTestToken } from './utils/auth';
import { setupTestEnv } from './utils/env';

describe('GPhotos Media Items Router', () => {
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

  describe('GET /api/v1/gphotos/media-items/:gMediaItemId', () => {
    it('should return 200 response when media item is successfully fetched', async () => {
      const mediaItem = {
        id: 'mediaItem1',
        description: 'Test media item',
        productUrl: 'https://example.com/mediaItem1/raw',
        baseUrl: 'https://example.com/mediaItem1',
        mimeType: 'image/jpeg',
        mediaMetadata: {
          creationTime: '2022-01-01T00:00:00Z',
          width: '1920',
          height: '1080',
          photo: {
            cameraMake: 'Canon',
            cameraModel: 'EOS 5D',
            focalLength: 50,
            apertureFNumber: 1.8,
            isoEquivalent: 400,
            exposureTime: '1/250s'
          }
        },
        filename: 'mediaItem1.jpg'
      };

      const client = mock<GPhotosClient>();
      client.getMediaItem.mockResolvedValue(mediaItem);

      const repo = mock<GPhotosClientsRepository>();
      repo.getGPhotosClientById.mockReturnValue(client);

      const app = express();
      app.use(await gPhotosMediaItemsRouter(repo));

      const res = await request(app)
        .get('/api/v1/gphotos/media-items/123:abc')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body).toEqual({
        baseUrl: 'https://example.com/mediaItem1',
        mimeType: 'image/jpeg',
        mediaMetadata: {
          creationTime: '2022-01-01T00:00:00Z',
          width: '1920',
          height: '1080',
          photo: {
            cameraMake: 'Canon',
            cameraModel: 'EOS 5D',
            focalLength: 50,
            apertureFNumber: 1.8,
            isoEquivalent: 400,
            exposureTime: '1/250s'
          }
        }
      });
    });

    it('should return 404 when the client is not found', async () => {
      const repo = mock<GPhotosClientsRepository>();
      repo.getGPhotosClientById.mockImplementation(() => {
        throw new NoGPhotosClientFoundError('123');
      });

      const app = express();
      app.use(await gPhotosMediaItemsRouter(repo));

      const res = await request(app)
        .get('/api/v1/gphotos/media-items/123:abc')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(404);
      expect(res.body).toEqual({ error: 'No GPhotos client found' });
    });

    it('should return 500 when there is an internal server error', async () => {
      const client = mock<GPhotosClient>();
      client.getMediaItem.mockImplementation(() => {
        throw new Error('Internal Server Error');
      });

      const repo = mock<GPhotosClientsRepository>();
      repo.getGPhotosClientById.mockReturnValue(client);

      const app = express();
      app.use(await gPhotosMediaItemsRouter(repo));

      const res = await request(app)
        .get('/api/v1/gphotos/media-items/123:abc')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(500);
      expect(res.body).toEqual({ error: 'Internal Server Error' });
    });

    it('should return 500 when Axios error is thrown', async () => {
      const axiosError = new AxiosError('Axios error');
      const client = mock<GPhotosClient>();
      client.getMediaItem.mockRejectedValue(axiosError);

      const repo = mock<GPhotosClientsRepository>();
      repo.getGPhotosClientById.mockReturnValue(client);

      const app = express();
      app.use(await gPhotosMediaItemsRouter(repo));

      const res = await request(app)
        .get('/api/v1/gphotos/media-items/123:abc')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(500);
      expect(res.body).toEqual({});
    });
  });
});
