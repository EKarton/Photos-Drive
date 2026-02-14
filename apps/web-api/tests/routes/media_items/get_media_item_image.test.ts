import { AxiosError } from 'axios';
import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import getMediaItemImageRouter from '../../../src/routes/media_items/get_media_item_image';
import { MediaItemsStore } from '../../../src/services/core/media_items/BaseMediaItemsStore';
import { MediaItem } from '../../../src/services/core/media_items/MediaItems';
import { GPhotosClient } from '../../../src/services/core/storage/gphotos/GPhotosClient';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../../../src/services/core/storage/gphotos/GPhotosClientsRepository';
import { fakeAuthEnv, generateTestToken } from '../utils/auth';
import { setupTestEnv } from '../utils/env';

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

const gPhotosMediaItem = {
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

describe('GET /api/v1/media-items/:id/image', () => {
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

  it('should return 302 response when media item is successfully fetched', async () => {
    const repo = mock<MediaItemsStore>();
    repo.getMediaItemById.mockResolvedValue(mockMediaItem);
    const client = mock<GPhotosClient>();
    client.getMediaItem.mockResolvedValue(gPhotosMediaItem);
    const gPhotosClientsRepository = mock<GPhotosClientsRepository>();
    gPhotosClientsRepository.getGPhotosClientById.mockReturnValue(client);
    const app = express();
    app.use(await getMediaItemImageRouter(repo, gPhotosClientsRepository));

    const res = await request(app)
      .get('/api/v1/media-items/mediaItemClientId1:mediaItem1/image')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(302);
    expect(res.headers.location).toEqual('https://example.com/mediaItem1');
  });

  it('should return 302 response when media item is successfully fetched with width and height params', async () => {
    const repo = mock<MediaItemsStore>();
    repo.getMediaItemById.mockResolvedValue(mockMediaItem);
    const client = mock<GPhotosClient>();
    client.getMediaItem.mockResolvedValue(gPhotosMediaItem);
    const gPhotosClientsRepository = mock<GPhotosClientsRepository>();
    gPhotosClientsRepository.getGPhotosClientById.mockReturnValue(client);
    const app = express();
    app.use(await getMediaItemImageRouter(repo, gPhotosClientsRepository));

    const res = await request(app)
      .get(
        '/api/v1/media-items/mediaItemClientId1:mediaItem1/image?width=100&height=200'
      )
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(302);
    expect(res.headers.location).toEqual(
      'https://example.com/mediaItem1=w100-h200'
    );
  });

  it('should return 400 when media item id is not valid', async () => {
    const repo = mock<MediaItemsStore>();
    const gPhotosClientsRepository = mock<GPhotosClientsRepository>();
    const app = express();
    app.use(await getMediaItemImageRouter(repo, gPhotosClientsRepository));

    const res = await request(app)
      .get(
        '/api/v1/media-items/mediaItemClientId1/image?width=100&height=200'
      )
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(400);
    expect(res.body).toEqual({ error: 'Invalid request' });
  });

  it('should return 400 when width is not valid', async () => {
    const repo = mock<MediaItemsStore>();
    const gPhotosClientsRepository = mock<GPhotosClientsRepository>();
    const app = express();
    app.use(await getMediaItemImageRouter(repo, gPhotosClientsRepository));

    const res = await request(app)
      .get(
        '/api/v1/media-items/mediaItemClientId1:mediaItem1/image?width=a&height=b'
      )
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(400);
    expect(res.body).toEqual({ error: 'Invalid request' });
  });

  it('should return 404 when client does not have base URL', async () => {
    const repo = mock<MediaItemsStore>();
    repo.getMediaItemById.mockResolvedValue(mockMediaItem);
    const client = mock<GPhotosClient>();
    client.getMediaItem.mockResolvedValue({
      ...gPhotosMediaItem,
      baseUrl: undefined
    });
    const gPhotosClientsRepository = mock<GPhotosClientsRepository>();
    gPhotosClientsRepository.getGPhotosClientById.mockReturnValue(client);
    const app = express();
    app.use(await getMediaItemImageRouter(repo, gPhotosClientsRepository));

    const res = await request(app)
      .get('/api/v1/media-items/mediaItemClientId1:mediaItem1/image')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(404);
    expect(res.body).toEqual({ error: 'Media item not found' });
  });

  it('should return 404 when the client is not found', async () => {
    const repo = mock<MediaItemsStore>();
    repo.getMediaItemById.mockResolvedValue(mockMediaItem);
    const gPhotosClientsRepository = mock<GPhotosClientsRepository>();
    gPhotosClientsRepository.getGPhotosClientById.mockImplementation(() => {
      throw new NoGPhotosClientFoundError('gPhotosClient1');
    });
    const app = express();
    app.use(await getMediaItemImageRouter(repo, gPhotosClientsRepository));

    const res = await request(app)
      .get('/api/v1/media-items/mediaItemClientId1:mediaItem1/image')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(404);
    expect(res.body).toEqual({ error: 'No GPhotos client found' });
  });

  it('should return 500 when there is an internal server error', async () => {
    const repo = mock<MediaItemsStore>();
    repo.getMediaItemById.mockResolvedValue(mockMediaItem);
    const gPhotosClientsRepository = mock<GPhotosClientsRepository>();
    const client = mock<GPhotosClient>();
    client.getMediaItem.mockImplementation(() => {
      throw new Error('Internal Server Error');
    });
    gPhotosClientsRepository.getGPhotosClientById.mockReturnValue(client);

    const app = express();
    app.use(await getMediaItemImageRouter(repo, gPhotosClientsRepository));

    const res = await request(app)
      .get('/api/v1/media-items/mediaItemClientId1:mediaItem1/image')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(500);
    expect(res.body).toEqual({ error: 'Internal Server Error' });
  });

  it('should return 500 when Axios error is thrown', async () => {
    const repo = mock<MediaItemsStore>();
    repo.getMediaItemById.mockResolvedValue(mockMediaItem);
    const gPhotosClientsRepository = mock<GPhotosClientsRepository>();
    const axiosError = new AxiosError('Axios error');
    const client = mock<GPhotosClient>();
    client.getMediaItem.mockRejectedValue(axiosError);
    gPhotosClientsRepository.getGPhotosClientById.mockReturnValue(client);

    const app = express();
    app.use(await getMediaItemImageRouter(repo, gPhotosClientsRepository));

    const res = await request(app)
      .get('/api/v1/media-items/mediaItemClientId1:mediaItem1/image')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(500);
    expect(res.body).toEqual({});
  });
});
