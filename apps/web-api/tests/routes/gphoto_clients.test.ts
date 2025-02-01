import { AxiosError } from 'axios';
import express from 'express';
import { mock } from 'jest-mock-extended';
import { importPKCS8, SignJWT } from 'jose';
import request from 'supertest';
import gPhotosClientsRouter from '../../src/routes/gphoto_clients';
import { GPhotosClient } from '../../src/services/blob_store/GPhotosClient';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../../src/services/blob_store/GPhotosClientsRepository';

describe('GPhoto Clients Router', () => {
  const originalEnv = process.env;
  const fakePublicKey =
    '-----BEGIN PUBLIC KEY-----MCowBQYDK2VwAyEADPItlNZv8oKHe/TVm4b04lfw1tvY8dde52zmWzk8hg4=-----END PUBLIC KEY-----%';
  const fakePrivateKey =
    '-----BEGIN PRIVATE KEY-----MC4CAQAwBQYDK2VwBCIEIG2LxwXdQJFmm2E3jNdvVoDzFp1EUisEuzteaAd3Wpw7-----END PRIVATE KEY-----%';
  let token = '';

  beforeEach(async () => {
    jest.resetModules();
    process.env = {
      ...originalEnv,
      ACCESS_TOKEN_JWT_PUBLIC_KEY: fakePublicKey,
      ACCESS_TOKEN_JWT_PRIVATE_KEY: fakePrivateKey
    };

    const secretKey = await importPKCS8(
      process.env.ACCESS_TOKEN_JWT_PRIVATE_KEY || '',
      'EdDSA'
    );
    const tokenExpiryTime = new Date(Date.now() + 360000);
    token = await new SignJWT({ id: '1' })
      .setProtectedHeader({ alg: 'EdDSA' })
      .setIssuedAt()
      .setIssuer('Photos-Map-Web-Api')
      .setAudience('http://localhost:3000')
      .setExpirationTime(tokenExpiryTime)
      .sign(secretKey);
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('GET /api/v1/gphotos/:clientId/media-items/:mediaItemId', () => {
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
      app.use(await gPhotosClientsRouter(repo));

      const res = await request(app)
        .get('/api/v1/gphotos/gPhotosClient1/media-items/mediaItem1')
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
        throw new NoGPhotosClientFoundError('gPhotosClient1');
      });

      const app = express();
      app.use(await gPhotosClientsRouter(repo));

      const res = await request(app)
        .get('/api/v1/gphotos/gPhotosClient1/media-items/mediaItem1')
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
      app.use(await gPhotosClientsRouter(repo));

      const res = await request(app)
        .get('/api/v1/gphotos/gPhotosClient1/media-items/mediaItem1')
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
      app.use(await gPhotosClientsRouter(repo));

      const res = await request(app)
        .get('/api/v1/gphotos/gPhotosClient1/media-items/mediaItem1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(500);
      expect(res.body).toEqual({});
    });
  });
});
