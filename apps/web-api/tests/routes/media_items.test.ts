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
  MediaItemsStore,
  SortByDirection,
  SortByField
} from '../../src/services/metadata_store/MediaItemsStore';
import { MongoDbClientNotFoundError } from '../../src/services/metadata_store/mongodb/MongoDbClientsStore';
import {
  BaseVectorStore,
  MediaItemEmbeddingId
} from '../../src/services/vector_stores/BaseVectorStore';
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

  describe('GET api/v1/media-items/search', () => {
    it('should return 200 with default params when query params are missing', async () => {
      const repo = mock<MediaItemsStore>();
      repo.listMediaItems.mockResolvedValue({
        mediaItems: MOCK_MEDIA_ITEMS,
        nextPageToken: undefined
      });
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .get('/api/v1/media-items/search')
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
      expect(repo.listMediaItems).toHaveBeenCalledWith(
        {
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

    it('should return 200 with query params populated', async () => {
      const repo = mock<MediaItemsStore>();
      repo.listMediaItems.mockResolvedValue({
        mediaItems: [],
        nextPageToken: 'next-token'
      });
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .get(
          '/api/v1/media-items/search?albumId=albumClient1:albumObject1&pageSize=10&pageToken=abc&sortBy=id&sortDir=asc&earliest=2025-01-01&latest=2025-04-01&latitude=-48&longitude=95&range=300'
        )
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toEqual({
        mediaItems: [],
        nextPageToken: 'next-token'
      });
      expect(repo.listMediaItems).toHaveBeenCalledWith(
        {
          albumId: {
            clientId: 'albumClient1',
            objectId: 'albumObject1'
          },
          earliestDateTaken: new Date('2025-01-01'),
          latestDateTaken: new Date('2025-04-01'),
          withinLocation: {
            latitude: -48,
            longitude: 95,
            range: 300
          },
          pageSize: 10,
          pageToken: 'abc',
          sortBy: {
            field: SortByField.ID,
            direction: SortByDirection.ASCENDING
          }
        },
        { abortController: expect.any(AbortController) }
      );
    });

    it('should return 500 when an unexpected error is thrown', async () => {
      const repo = mock<MediaItemsStore>();
      repo.listMediaItems.mockRejectedValue(new Error('Something went wrong'));
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .get('/api/v1/media-items/search')
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
      const repo = mock<MediaItemsStore>();
      repo.getMediaItemById.mockResolvedValue(mockMediaItem);
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(await mediaItemsRouter(repo, vectorStore));

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
      const repo = mock<MediaItemsStore>();
      repo.getMediaItemById.mockRejectedValue(
        new MongoDbClientNotFoundError('mediaItemClientId1:mediaItem1')
      );
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(await mediaItemsRouter(repo, vectorStore));

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
      const repo = mock<MediaItemsStore>();
      repo.getMediaItemById.mockRejectedValue(
        new MediaItemNotFoundError(mediaItemId)
      );
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(404);
      expect(res.body).toEqual({ error: 'Media item not found' });
    });

    it('should return 500 response given MediaItemsRepository returns random error', async () => {
      const repo = mock<MediaItemsStore>();
      repo.getMediaItemById.mockRejectedValue(new Error('Random error'));
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(500);
      expect(res.body).toEqual({});
    });
  });

  describe('POST /api/v1/media-items/vector-search', () => {
    it('should return 200 with matching media items', async () => {
      const repo = mock<MediaItemsStore>();
      const vectorStore = mock<BaseVectorStore>();

      vectorStore.getReleventMediaItemEmbeddings.mockResolvedValue([
        {
          id: new MediaItemEmbeddingId(
            new Object().toString(),
            new Object().toString()
          ),
          mediaItemId: MOCK_MEDIA_ITEMS[0].id,
          embedding: new Float32Array([0.1, 0.2, 0.3]),
          dateTaken: new Date(0)
        },
        {
          id: new MediaItemEmbeddingId(
            new Object().toString(),
            new Object().toString()
          ),
          mediaItemId: MOCK_MEDIA_ITEMS[1].id,
          embedding: new Float32Array([0.1, 0.2, 0.3]),
          dateTaken: new Date(0)
        }
      ]);
      // Mimic bulkGetMediaItemByIds returning media item IDs not in order
      repo.bulkGetMediaItemByIds.mockResolvedValue([
        MOCK_MEDIA_ITEMS[1],
        MOCK_MEDIA_ITEMS[0]
      ]);

      const app = express();
      app.use(express.json());
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .post('/api/v1/media-items/vector-search')
        .set('Authorization', `Bearer ${token}`)
        .send({ queryEmbedding: new Float32Array([0.1, 0.2, 0.3]) });

      expect(res.statusCode).toBe(200);
      expect(res.body).toEqual({
        mediaItems: [
          {
            id: 'albumClient1:mediaItem1',
            fileName: 'dog.png',
            location: { latitude: 123, longitude: 456 },
            gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
            albumId: 'albumClient1:albumObject1',
            width: 1000,
            height: 2000,
            dateTaken: '2025-06-07T17:00:00.000Z'
          },
          {
            id: 'albumClient1:mediaItem2',
            fileName: 'cat.png',
            location: { latitude: 123, longitude: 456 },
            gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
            albumId: 'albumClient1:albumObject1',
            width: 100,
            height: 200,
            dateTaken: '2024-06-07T17:00:00.000Z'
          }
        ]
      });
    });

    it('should return 400 if query is missing', async () => {
      const repo = mock<MediaItemsStore>();
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(express.json());
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .post('/api/v1/media-items/vector-search')
        .set('Authorization', `Bearer ${token}`)
        .send({});

      expect(res.statusCode).toBe(400);
      expect(res.body).toEqual({
        error: 'Missing or invalid "queryEmbedding" field'
      });
    });

    it('should return 400 for invalid earliestDateTaken format', async () => {
      const repo = mock<MediaItemsStore>();
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(express.json());
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .post('/api/v1/media-items/vector-search')
        .set('Authorization', `Bearer ${token}`)
        .send({
          queryEmbedding: new Float32Array([1, 2, 3]),
          earliestDateTaken: 'invalid-date'
        });

      expect(res.statusCode).toBe(400);
      expect(res.body).toEqual({ error: 'Invalid earliestDateTaken format' });
    });

    it('should return 400 for invalid latestDateTaken format', async () => {
      const repo = mock<MediaItemsStore>();
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(express.json());
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .post('/api/v1/media-items/vector-search')
        .set('Authorization', `Bearer ${token}`)
        .send({
          queryEmbedding: new Float32Array([1, 2, 3]),
          latestDateTaken: 'invalid-date'
        });

      expect(res.statusCode).toBe(400);
      expect(res.body).toEqual({ error: 'Invalid latestDateTaken format' });
    });

    it('should pass filters and topK to vectorStore', async () => {
      const repo = mock<MediaItemsStore>();
      const vectorStore = mock<BaseVectorStore>();

      vectorStore.getReleventMediaItemEmbeddings.mockResolvedValue([]);
      repo.bulkGetMediaItemByIds.mockResolvedValue([]);

      const app = express();
      app.use(express.json());
      app.use(await mediaItemsRouter(repo, vectorStore));

      const earliest = '2025-01-01T00:00:00.000Z';
      const latest = '2025-01-02T00:00:00.000Z';

      await request(app)
        .post('/api/v1/media-items/vector-search')
        .set('Authorization', `Bearer ${token}`)
        .send({
          queryEmbedding: new Float32Array([1, 2, 3]),
          earliestDateTaken: earliest,
          latestDateTaken: latest,
          withinMediaItemIds: ['albumClient1:mediaItem1'],
          topK: 5
        });

      expect(vectorStore.getReleventMediaItemEmbeddings).toHaveBeenCalledWith(
        expect.objectContaining({
          startDateTaken: new Date(earliest),
          endDateTaken: new Date(latest),
          withinMediaItemIds: [
            { clientId: 'albumClient1', objectId: 'mediaItem1' }
          ],
          topK: 5
        }),
        expect.any(Object)
      );
    });

    it('should return 500 if vector store throws', async () => {
      const repo = mock<MediaItemsStore>();
      const vectorStore = mock<BaseVectorStore>();

      vectorStore.getReleventMediaItemEmbeddings.mockRejectedValue(
        new Error('Internal fail')
      );

      const app = express();
      app.use(express.json());
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .post('/api/v1/media-items/vector-search')
        .set('Authorization', `Bearer ${token}`)
        .send({ queryEmbedding: new Float32Array([1, 2, 3]) });

      expect(res.statusCode).toBe(500);
    });
  });

  describe('POST /api/v1/media-items/bulk-get', () => {
    it('should return 200 with media items', async () => {
      const repo = mock<MediaItemsStore>();
      const vectorStore = mock<BaseVectorStore>();

      repo.bulkGetMediaItemByIds.mockResolvedValue(MOCK_MEDIA_ITEMS);

      const app = express();
      app.use(express.json());
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .post('/api/v1/media-items/bulk-get')
        .set('Authorization', `Bearer ${token}`)
        .send({
          mediaItemIds: ['albumClient1:mediaItem1', 'albumClient1:mediaItem2']
        });

      expect(res.statusCode).toBe(200);
      expect(res.body).toEqual({
        mediaItems: [
          {
            id: 'albumClient1:mediaItem1',
            fileName: 'dog.png',
            location: { latitude: 123, longitude: 456 },
            gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
            albumId: 'albumClient1:albumObject1',
            width: 1000,
            height: 2000,
            dateTaken: '2025-06-07T17:00:00.000Z'
          },
          {
            id: 'albumClient1:mediaItem2',
            fileName: 'cat.png',
            location: { latitude: 123, longitude: 456 },
            gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
            albumId: 'albumClient1:albumObject1',
            width: 100,
            height: 200,
            dateTaken: '2024-06-07T17:00:00.000Z'
          }
        ]
      });
    });

    it('should return 413 if there are too many media items to request for', async () => {
      const repo = mock<MediaItemsStore>();
      const vectorStore = mock<BaseVectorStore>();

      const app = express();
      app.use(express.json());
      app.use(await mediaItemsRouter(repo, vectorStore));

      const tooManyIds = new Array(51).fill('albumClient1:mediaItem1');

      const res = await request(app)
        .post('/api/v1/media-items/bulk-get')
        .set('Authorization', `Bearer ${token}`)
        .send({
          mediaItemIds: tooManyIds
        });

      expect(res.statusCode).toBe(413);
      expect(res.body).toEqual({
        error: 'Too many media item IDs to fetch (needs to be under 50)'
      });
      // Ensure repo method was never called
      expect(repo.bulkGetMediaItemByIds).not.toHaveBeenCalled();
    });

    it('should return 500 if there is an error with fetching media items', async () => {
      const repo = mock<MediaItemsStore>();
      const vectorStore = mock<BaseVectorStore>();

      repo.bulkGetMediaItemByIds.mockRejectedValue(
        new Error('Database failure')
      );

      const app = express();
      app.use(express.json());
      app.use(await mediaItemsRouter(repo, vectorStore));

      const res = await request(app)
        .post('/api/v1/media-items/bulk-get')
        .set('Authorization', `Bearer ${token}`)
        .send({
          mediaItemIds: ['albumClient1:mediaItem1']
        });

      expect(res.statusCode).toBe(500);
    });
  });
});
