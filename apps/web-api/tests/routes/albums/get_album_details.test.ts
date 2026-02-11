import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import getAlbumDetailsRouter from '../../../src/routes/albums/get_album_details';
import { Album, AlbumId } from '../../../src/services/metadata_store/Albums';
import {
  AlbumNotFoundError,
  AlbumsStore
} from '../../../src/services/metadata_store/AlbumsStore';
import { MediaItemsStore } from '../../../src/services/metadata_store/MediaItemsStore';
import { MongoDbClientNotFoundError } from '../../../src/services/metadata_store/mongodb/MongoDbClientsStore';
import { fakeAuthEnv, generateTestToken } from '../utils/auth';
import { setupTestEnv } from '../utils/env';

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

describe('GET api/v1/albums/:albumId', () => {
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

  it('should return 200 with correct body response, given correct parameters', async () => {
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.getAlbumById.mockResolvedValue(MOCK_ALBUM);
    mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
    mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);
    const app = express();
    app.use(
      await getAlbumDetailsRouter(
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
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.getAlbumById.mockResolvedValue({
      ...MOCK_ALBUM,
      parent_album_id: undefined
    });
    mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
    mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);
    const app = express();
    app.use(
      await getAlbumDetailsRouter(
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
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.getAlbumById.mockResolvedValue(MOCK_ROOT_ALBUM);
    mockAlbumsRepository.getNumAlbumsInAlbum.mockResolvedValue(1);
    mockMediaItemsRepository.getNumMediaItemsInAlbum.mockResolvedValue(2);
    const app = express();
    app.use(
      await getAlbumDetailsRouter(
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
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.getAlbumById.mockRejectedValue(
      new MongoDbClientNotFoundError('albumClient1:albumObject2')
    );
    const app = express();
    app.use(
      await getAlbumDetailsRouter(
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
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.getAlbumById.mockRejectedValue(
      new AlbumNotFoundError({
        clientId: 'albumClient1',
        objectId: 'albumObject2'
      })
    );
    const app = express();
    app.use(
      await getAlbumDetailsRouter(
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
    const mockAlbumsRepository = mock<AlbumsStore>();
    const mockMediaItemsRepository = mock<MediaItemsStore>();
    mockAlbumsRepository.getAlbumById.mockRejectedValue(
      new Error('Random error')
    );
    const app = express();
    app.use(
      await getAlbumDetailsRouter(
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
