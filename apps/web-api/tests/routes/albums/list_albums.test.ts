import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import listAlbumsRouter from '../../../src/routes/albums/list_albums';
import { Album, AlbumId } from '../../../src/services/core/albums/Albums';
import { AlbumsStore } from '../../../src/services/core/albums/BaseAlbumsStore';
import {
  MediaItemsStore,
  SortByDirection,
  SortByField
} from '../../../src/services/core/media_items/BaseMediaItemsStore';
import { fakeAuthEnv, generateTestToken } from '../utils/auth';
import { setupTestEnv } from '../utils/env';

const MOCK_ROOT_ALBUM_ID: AlbumId = {
  clientId: 'albumClient1',
  objectId: 'albumObject0'
};

const MOCK_ALBUM: Album = {
  id: {
    clientId: 'albumClient1',
    objectId: 'albumObject1'
  },
  name: 'Photos',
  parent_album_id: MOCK_ROOT_ALBUM_ID
};

describe('GET /api/v1/albums', () => {
  let cleanupTestEnvFn = () => { };
  let token = '';

  beforeEach(async () => {
    jest.resetModules();
    cleanupTestEnvFn = setupTestEnv({ ...fakeAuthEnv });
    token = await generateTestToken();
  });

  afterEach(() => {
    cleanupTestEnvFn();
  });

  it('should return 200 with default pageSize and sort when no query params are provided', async () => {
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.listAlbums.mockResolvedValue({
      albums: [MOCK_ALBUM],
      nextPageToken: undefined
    });
    mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
    mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);
    const app = express();
    app.use(
      await listAlbumsRouter(
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
    expect(mockAlbumsRepository.listAlbums).toHaveBeenCalledWith(
      {
        parentAlbumId: undefined,
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

  it('should return 200 with query parameters pageSize, pageToken, sortBy, sortDir, and parentAlbumId', async () => {
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.listAlbums.mockResolvedValue({
      albums: [MOCK_ALBUM],
      nextPageToken: 'nextToken'
    });
    mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
    mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);
    const app = express();
    app.use(
      await listAlbumsRouter(
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
    expect(mockAlbumsRepository.listAlbums).toHaveBeenCalledWith(
      {
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
      },
      { abortController: expect.any(AbortController) }
    );
  });

  it('should return 200 with parentAlbumId set to root', async () => {
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.listAlbums.mockResolvedValue({
      albums: [MOCK_ALBUM],
      nextPageToken: undefined
    });
    mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
    mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);
    const app = express();
    app.use(
      await listAlbumsRouter(
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
    expect(mockAlbumsRepository.listAlbums).toHaveBeenCalledWith(
      {
        parentAlbumId: MOCK_ROOT_ALBUM_ID,
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

  it('should return 500 when albumsRepo.listAlbums throws unexpected error', async () => {
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.listAlbums.mockRejectedValue(
      new Error('Unexpected error')
    );
    const app = express();
    app.use(
      await listAlbumsRouter(
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

  it('should return 400 when query parameters are invalid', async () => {
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    const app = express();
    app.use(
      await listAlbumsRouter(
        MOCK_ROOT_ALBUM_ID,
        mockAlbumsRepository,
        mockMediaItemsRepository
      )
    );

    const res = await request(app)
      .get('/api/v1/albums?pageSize=1000')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'Invalid query parameters' });
  });
});
