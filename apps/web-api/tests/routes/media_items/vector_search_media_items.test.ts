import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import vectorSearchMediaItemsRouter from '../../../src/routes/media_items/vector_search_media_items';
import { MediaItem } from '../../../src/services/metadata_store/MediaItems';
import { MediaItemsStore } from '../../../src/services/metadata_store/MediaItemsStore';
import {
  BaseVectorStore,
  MediaItemEmbeddingId
} from '../../../src/services/vector_stores/BaseVectorStore';
import { fakeAuthEnv, generateTestToken } from '../utils/auth';
import { setupTestEnv } from '../utils/env';

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

describe('POST /api/v1/media-items/vector-search', () => {
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
        score: 0.9
      },
      {
        id: new MediaItemEmbeddingId(
          new Object().toString(),
          new Object().toString()
        ),
        mediaItemId: MOCK_MEDIA_ITEMS[1].id,
        score: 0.8
      }
    ]);
    // Mimic bulkGetMediaItemByIds returning media item IDs not in order
    repo.bulkGetMediaItemByIds.mockResolvedValue([
      MOCK_MEDIA_ITEMS[1],
      MOCK_MEDIA_ITEMS[0]
    ]);
    const app = express();
    app.use(express.json());
    app.use(await vectorSearchMediaItemsRouter(repo, vectorStore));

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
    app.use(await vectorSearchMediaItemsRouter(repo, vectorStore));

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
    app.use(await vectorSearchMediaItemsRouter(repo, vectorStore));

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
    app.use(await vectorSearchMediaItemsRouter(repo, vectorStore));

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
    app.use(await vectorSearchMediaItemsRouter(repo, vectorStore));

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
    app.use(await vectorSearchMediaItemsRouter(repo, vectorStore));

    const res = await request(app)
      .post('/api/v1/media-items/vector-search')
      .set('Authorization', `Bearer ${token}`)
      .send({ queryEmbedding: new Float32Array([1, 2, 3]) });

    expect(res.statusCode).toBe(500);
  });
});
