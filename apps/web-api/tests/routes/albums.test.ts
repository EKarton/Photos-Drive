import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import albumsRouter from '../../src/routes/albums';
import { Album, AlbumId } from '../../src/services/metadata_store/Albums';
import {
  AlbumNotFoundError,
  AlbumsRepository
} from '../../src/services/metadata_store/AlbumsRepository';
import { MediaItem } from '../../src/services/metadata_store/MediaItems';
import { MediaItemsRepository } from '../../src/services/metadata_store/MediaItemsRepository';
import { MongoDbClientNotFoundError } from '../../src/services/metadata_store/MongoDbClientsRepository';
import { fakeAuthEnv, generateTestToken } from './utils/auth';
import { setupTestEnv } from './utils/env';

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
  ]
};

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
    }
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
    }
  }
];

describe('Albums Router', () => {
  let cleanupTestEnvFn = () => {};
  let token = '';

  beforeEach(async () => {
    jest.resetModules();
    cleanupTestEnvFn = setupTestEnv({ ...fakeAuthEnv });
    token = await generateTestToken();
  });

  afterEach(() => {
    cleanupTestEnvFn();
  });

  describe('GET api/v1/albums/:albumId', () => {
    it('should return 200 with correct body response, given correct parameters', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.getAlbumById.mockResolvedValue(MOCK_ALBUM);
      mockMediaItemsRepository.getMediaItemsInAlbum.mockResolvedValue(
        MOCK_MEDIA_ITEMS
      );
      const app = express();
      app.use(
        await albumsRouter(
          MOCK_ROOT_ALBUM_ID,
          mockAlbumsRepository,
          mockMediaItemsRepository
        )
      );

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
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.getAlbumById.mockResolvedValue({
        ...MOCK_ALBUM,
        parent_album_id: undefined
      });
      mockMediaItemsRepository.getMediaItemsInAlbum.mockResolvedValue(
        MOCK_MEDIA_ITEMS
      );
      const app = express();
      app.use(
        await albumsRouter(
          MOCK_ROOT_ALBUM_ID,
          mockAlbumsRepository,
          mockMediaItemsRepository
        )
      );

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
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.getAlbumById.mockRejectedValue(
        new MongoDbClientNotFoundError('albumClient1:albumObject2')
      );
      const app = express();
      app.use(
        await albumsRouter(
          MOCK_ROOT_ALBUM_ID,
          mockAlbumsRepository,
          mockMediaItemsRepository
        )
      );

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
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.getAlbumById.mockRejectedValue(
        new AlbumNotFoundError(MOCK_ALBUM.child_album_ids[0])
      );
      const app = express();
      app.use(
        await albumsRouter(
          MOCK_ROOT_ALBUM_ID,
          mockAlbumsRepository,
          mockMediaItemsRepository
        )
      );

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
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.getAlbumById.mockRejectedValue(
        new Error('Random error')
      );
      const app = express();
      app.use(
        await albumsRouter(
          MOCK_ROOT_ALBUM_ID,
          mockAlbumsRepository,
          mockMediaItemsRepository
        )
      );

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
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.getAlbumById.mockResolvedValue(MOCK_ALBUM);
      mockMediaItemsRepository.getMediaItemsInAlbum.mockResolvedValue(
        MOCK_MEDIA_ITEMS
      );
      const app = express();
      app.use(
        await albumsRouter(
          MOCK_ROOT_ALBUM_ID,
          mockAlbumsRepository,
          mockMediaItemsRepository
        )
      );

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
