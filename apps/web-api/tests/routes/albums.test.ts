import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import albumsRouter from '../../src/routes/albums';
import { Album, AlbumId } from '../../src/services/metadata_store/Albums';
import {
  AlbumNotFoundError,
  AlbumsRepository
} from '../../src/services/metadata_store/AlbumsRepository';
import {
  MediaItemsRepository,
  SortByDirection,
  SortByField
} from '../../src/services/metadata_store/MediaItemsRepository';
import { MongoDbClientNotFoundError } from '../../src/services/metadata_store/mongodb/MongoDbClientsRepository';
import { fakeAuthEnv, generateTestToken } from './utils/auth';
import { setupTestEnv } from './utils/env';

const MOCK_ROOT_ALBUM_ID: AlbumId = {
  clientId: 'albumClient1',
  objectId: 'albumObject0'
};

const MOCK_ROOT_ALBUM: Album = {
  id: MOCK_ROOT_ALBUM_ID,
  name: 'Archives',
  parent_album_id: undefined
};

const MOCK_ALBUM: Album = {
  id: {
    clientId: 'albumClient1',
    objectId: 'albumObject1'
  },
  name: 'Photos',
  parent_album_id: MOCK_ROOT_ALBUM_ID
};

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
      mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
      mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);
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
        numChildAlbums: 1,
        numMediaItems: 2
      });
    });

    it('should return 200 with correct body response when requesting for album without parent album ID', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.getAlbumById.mockResolvedValue({
        ...MOCK_ALBUM,
        parent_album_id: undefined
      });
      mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
      mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);
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
        numChildAlbums: 1,
        numMediaItems: 2
      });
    });

    it('should return 200 given albumId is set to root', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.getAlbumById.mockResolvedValue(MOCK_ROOT_ALBUM);
      mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
      mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);
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

      expect(res.statusCode).toEqual(200);
      expect(res.body).toEqual({
        id: 'albumClient1:albumObject0',
        albumName: 'Archives',
        parentAlbumId: null,
        numChildAlbums: 1,
        numMediaItems: 2
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
        new AlbumNotFoundError({
          clientId: 'albumClient1',
          objectId: 'albumObject2'
        })
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

  describe('GET /api/v1/albums', () => {
    it('should return 200 with default pageSize and sort when no query params are provided', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.listAlbums.mockResolvedValue({
        albums: [MOCK_ALBUM],
        nextPageToken: undefined
      });
      mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
      mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);

      const app = express();
      app.use(
        await albumsRouter(
          MOCK_ROOT_ALBUM_ID,
          mockAlbumsRepository,
          mockMediaItemsRepository
        )
      );

      const res = await request(app)
        .get('/api/v1/albums')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toEqual({
        albums: [
          {
            id: 'albumClient1:albumObject1',
            albumName: 'Photos',
            parentAlbumId: 'albumClient1:albumObject0',
            numChildAlbums: 1,
            numMediaItems: 2
          }
        ]
      });

      expect(mockAlbumsRepository.listAlbums).toHaveBeenCalledWith({
        parentAlbumId: undefined,
        pageSize: 25,
        pageToken: undefined,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });
    });

    it('should return 200 with query parameters pageSize, pageToken, sortBy, sortDir, and parentAlbumId', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.listAlbums.mockResolvedValue({
        albums: [MOCK_ALBUM],
        nextPageToken: 'nextToken'
      });
      mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
      mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);

      const app = express();
      app.use(
        await albumsRouter(
          MOCK_ROOT_ALBUM_ID,
          mockAlbumsRepository,
          mockMediaItemsRepository
        )
      );

      const res = await request(app)
        .get(
          '/api/v1/albums?pageSize=5&pageToken=abc%2Fdef&sortBy=id&sortDir=desc&parentAlbumId=albumClient1:albumObject0'
        )
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toEqual({
        albums: [
          {
            id: 'albumClient1:albumObject1',
            albumName: 'Photos',
            parentAlbumId: 'albumClient1:albumObject0',
            numChildAlbums: 1,
            numMediaItems: 2
          }
        ],
        nextPageToken: 'nextToken'
      });

      expect(mockAlbumsRepository.listAlbums).toHaveBeenCalledWith({
        parentAlbumId: {
          clientId: 'albumClient1',
          objectId: 'albumObject0'
        },
        pageSize: 5,
        pageToken: 'abc/def',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.DESCENDING
        }
      });
    });

    it('should return 200 with parentAlbumId set to root', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.listAlbums.mockResolvedValue({
        albums: [MOCK_ALBUM],
        nextPageToken: undefined
      });
      mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
      mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);

      const app = express();
      app.use(
        await albumsRouter(
          MOCK_ROOT_ALBUM_ID,
          mockAlbumsRepository,
          mockMediaItemsRepository
        )
      );

      const res = await request(app)
        .get('/api/v1/albums?parentAlbumId=root')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toEqual({
        albums: [
          {
            id: 'albumClient1:albumObject1',
            albumName: 'Photos',
            parentAlbumId: 'albumClient1:albumObject0',
            numChildAlbums: 1,
            numMediaItems: 2
          }
        ]
      });

      expect(mockAlbumsRepository.listAlbums).toHaveBeenCalledWith({
        parentAlbumId: undefined,
        pageSize: 25,
        pageToken: undefined,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });
    });

    it('should return 500 when albumsRepo.listAlbums throws unexpected error', async () => {
      const mockAlbumsRepository = mock<AlbumsRepository>();
      const mockMediaItemsRepository = mock<MediaItemsRepository>();
      mockAlbumsRepository.listAlbums.mockRejectedValue(
        new Error('Unexpected error')
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
        .get('/api/v1/albums')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(500);
    });
  });
});
