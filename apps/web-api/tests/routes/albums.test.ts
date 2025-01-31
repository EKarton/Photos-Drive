import express from 'express';
import { mock } from 'jest-mock-extended';
import { importPKCS8, SignJWT } from 'jose';
import request from 'supertest';
import albumsRouter from '../../src/routes/albums';
import { Album, AlbumId } from '../../src/services/metadata_store/Albums';
import {
  AlbumNotFoundError,
  AlbumsRepository
} from '../../src/services/metadata_store/AlbumsRepository';
import { MongoDbClientNotFoundError } from '../../src/services/metadata_store/MongoDbClientsRepository';

const MOCK_ROOT_ALBUM_ID: AlbumId = {
  clientId: 'albumClient1',
  objectId: 'albumObject1'
};

const MOCK_ALBUM: Album = {
  id: {
    clientId: 'albumClient1',
    objectId: 'albumObject1'
  },
  name: 'Photos',
  parent_album_id: {
    clientId: 'albumClient1',
    objectId: 'albumObject0'
  },
  child_album_ids: [
    {
      clientId: 'albumClient1',
      objectId: 'albumObject2'
    }
  ],
  media_item_ids: [
    {
      clientId: 'albumClient1',
      objectId: 'mediaItem1'
    },
    {
      clientId: 'albumClient1',
      objectId: 'mediaItem2'
    }
  ]
};

describe('Albums Router', () => {
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

  describe('GET api/v1/albums/:albumId', () => {
    it('should return 200 with correct body response, given correct parameters', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      mockAlbumsRepository.getAlbumById.mockResolvedValue(MOCK_ALBUM);
      const app = express();
      app.use(await albumsRouter(MOCK_ROOT_ALBUM_ID, mockAlbumsRepository));

      const res = await request(app)
        .get('/api/v1/albums/albumClient1:albumObject1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body).toEqual({
        id: 'albumClient1:albumObject1',
        albumName: 'Photos',
        parentAlbumId: 'albumClient1:albumObject0',
        childAlbumIds: ['albumClient1:albumObject2'],
        mediaItemIds: ['albumClient1:mediaItem1', 'albumClient1:mediaItem2']
      });
    });

    it('should return 200 with correct body response when requesting for album without parent album ID', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      mockAlbumsRepository.getAlbumById.mockResolvedValue({
        ...MOCK_ALBUM,
        parent_album_id: undefined
      });
      const app = express();
      app.use(await albumsRouter(MOCK_ROOT_ALBUM_ID, mockAlbumsRepository));

      const res = await request(app)
        .get('/api/v1/albums/albumClient1:albumObject1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body).toEqual({
        id: 'albumClient1:albumObject1',
        albumName: 'Photos',
        parentAlbumId: null,
        childAlbumIds: ['albumClient1:albumObject2'],
        mediaItemIds: ['albumClient1:mediaItem1', 'albumClient1:mediaItem2']
      });
    });

    it(`should return error code, given MongoDbClientNotFoundError thrown from AlbumsRepository`, async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      mockAlbumsRepository.getAlbumById.mockRejectedValue(
        new MongoDbClientNotFoundError('albumClient1:albumObject2')
      );
      const app = express();
      app.use(await albumsRouter(MOCK_ROOT_ALBUM_ID, mockAlbumsRepository));

      const res = await request(app)
        .get('/api/v1/albums/albumClient1:albumObject1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(404);
      expect(res.body).toEqual({
        error: 'Album not found'
      });
    });

    it(`should return error code, given MongoDbClientNotFoundError thrown from AlbumsRepository`, async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      mockAlbumsRepository.getAlbumById.mockRejectedValue(
        new AlbumNotFoundError(MOCK_ALBUM.child_album_ids[0])
      );
      const app = express();
      app.use(await albumsRouter(MOCK_ROOT_ALBUM_ID, mockAlbumsRepository));

      const res = await request(app)
        .get('/api/v1/albums/albumClient1:albumObject1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(404);
      expect(res.body).toEqual({
        error: 'Album not found'
      });
    });

    it('should return error code, given random error thrown from AlbumsRepository', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      mockAlbumsRepository.getAlbumById.mockRejectedValue(
        new Error('Random error')
      );
      const app = express();
      app.use(await albumsRouter(MOCK_ROOT_ALBUM_ID, mockAlbumsRepository));

      const res = await request(app)
        .get('/api/v1/albums/albumClient1:albumObject1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(500);
      expect(res.body).toEqual({});
    });
  });

  describe('GET api/v1/albums/root', () => {
    it('should return 302', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      mockAlbumsRepository.getAlbumById.mockResolvedValue(MOCK_ALBUM);
      const app = express();
      app.use(await albumsRouter(MOCK_ROOT_ALBUM_ID, mockAlbumsRepository));

      const res = await request(app)
        .get('/api/v1/albums/root')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(302);
      expect(res.headers['location']).toEqual(
        '/api/v1/albums/albumClient1:albumObject1'
      );
    });
  });
});
