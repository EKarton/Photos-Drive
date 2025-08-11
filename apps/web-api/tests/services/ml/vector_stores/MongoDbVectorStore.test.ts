import { jest } from '@jest/globals';
import { Binary, MongoClient, ObjectId } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { convertStringToMediaItemId } from '../../../../src/services/metadata_store/MediaItems';
import {
  MediaItemEmbeddingId,
  QueryMediaItemEmbeddingRequest
} from '../../../../src/services/ml/vector_stores/BaseVectorStore';
import { MongoDbVectorStore } from '../../../../src/services/ml/vector_stores/MongoDbVectorStore';

describe('MongoDbVectorStore', () => {
  let mongoServer: MongoMemoryServer;
  let mongoClient: MongoClient;

  let store: MongoDbVectorStore;
  const dbName = 'testdb';
  const collectionName = 'testcollection';
  const storeId = 'test-store';

  beforeAll(async () => {
    mongoServer = await MongoMemoryServer.create();
    mongoClient = await MongoClient.connect(mongoServer.getUri());

    store = new MongoDbVectorStore(
      storeId,
      mongoClient,
      dbName,
      collectionName
    );
  });

  beforeEach(async () => {
    await mongoClient.db(dbName).collection(collectionName).deleteMany({});
    jest.restoreAllMocks();
  });

  afterAll(async () => {
    if (mongoClient) {
      await mongoClient.close(true);
    }
    if (mongoServer) {
      await mongoServer.stop({ force: true });
    }
  });

  it('getStoreId returns the store id', () => {
    expect(store.getStoreId()).toBe(storeId);
  });

  describe('getEmbeddingById', () => {
    it('returns a parsed MediaItemEmbedding when found', async () => {
      const _id = new ObjectId();
      const embeddingArray = new Float32Array([0.1, 0.2, 0.3]);
      const doc = {
        _id,
        embedding: Binary.fromFloat32Array(embeddingArray),
        media_item_id: '407f1f77bcf86cd799439013:507f1f77bcf86cd799439013',
        date_taken: new Date('2022-01-01')
      };
      await mongoClient.db(dbName).collection(collectionName).insertOne(doc);

      const result = await store.getEmbeddingById(
        new MediaItemEmbeddingId(storeId, _id.toHexString())
      );

      expect(result.embedding).toEqual(embeddingArray);
      expect(result).toEqual({
        dateTaken: new Date('2022-01-01T00:00:00.000Z'),
        embedding: new Float32Array([
          0.10000000149011612, 0.20000000298023224, 0.30000001192092896
        ]),
        id: new MediaItemEmbeddingId('test-store', _id.toString()),
        mediaItemId: {
          clientId: '407f1f77bcf86cd799439013',
          objectId: '507f1f77bcf86cd799439013'
        }
      });
    });

    it('throws when no document found', async () => {
      await expect(
        store.getEmbeddingById(
          new MediaItemEmbeddingId(storeId, new ObjectId().toHexString())
        )
      ).rejects.toThrow(/Cannot find embedding/);
    });
  });

  describe('getReleventMediaItemEmbeddings', () => {
    it('returns parsed embeddings from aggregation pipeline', async () => {
      const doc1 = {
        _id: new ObjectId(),
        embedding: Binary.fromFloat32Array(new Float32Array([0.1, 0.2, 0.3])),
        media_item_id: '407f1f77bcf86cd799439011:507f1f77bcf86cd799439011',
        date_taken: new Date('2022-01-01')
      };
      const doc2 = {
        _id: new ObjectId(),
        embedding: Binary.fromFloat32Array(new Float32Array([0.4, 0.5, 0.6])),
        media_item_id: '407f1f77bcf86cd799439012:507f1f77bcf86cd799439012',
        date_taken: new Date('2022-02-01')
      };

      // Mock aggregate() to fake Atlas vector search results
      jest.spyOn(store['_collection'], 'aggregate').mockReturnValue({
        [Symbol.asyncIterator]: async function* () {
          yield doc1;
          yield doc2;
        }
      } as never);

      const query: QueryMediaItemEmbeddingRequest = {
        embedding: new Float32Array([1.1, 1.2, 1.3]),
        startDateTaken: new Date('2021-01-01'),
        endDateTaken: new Date('2023-01-01'),
        withinMediaItemIds: [
          convertStringToMediaItemId(
            '407f1f77bcf86cd799439011:507f1f77bcf86cd799439011'
          ),
          convertStringToMediaItemId(
            '407f1f77bcf86cd799439012:507f1f77bcf86cd799439012'
          )
        ],
        topK: 2
      };

      const results = await store.getReleventMediaItemEmbeddings(query);
      expect(results).toHaveLength(2);
      expect(results[0].id).toBeInstanceOf(MediaItemEmbeddingId);
      expect(typeof results[0].dateTaken.getTime()).toBe('number');
    });

    it('returns parsed embeddings that do not contain date_taken fields', async () => {
      const doc1 = {
        _id: new ObjectId(),
        embedding: Binary.fromFloat32Array(new Float32Array([0.1, 0.2, 0.3])),
        media_item_id: '407f1f77bcf86cd799439011:507f1f77bcf86cd799439011'
      };
      const doc2 = {
        _id: new ObjectId(),
        embedding: Binary.fromFloat32Array(new Float32Array([0.4, 0.5, 0.6])),
        media_item_id: '407f1f77bcf86cd799439012:507f1f77bcf86cd799439012'
      };

      // Mock aggregate() to fake Atlas vector search results
      jest.spyOn(store['_collection'], 'aggregate').mockReturnValue({
        [Symbol.asyncIterator]: async function* () {
          yield doc1;
          yield doc2;
        }
      } as never);

      const query: QueryMediaItemEmbeddingRequest = {
        embedding: new Float32Array([1.1, 1.2, 1.3]),
        topK: 2
      };

      const results = await store.getReleventMediaItemEmbeddings(query);
      expect(results).toEqual([
        {
          dateTaken: new Date('1970-01-01T00:00:00.000Z'),
          embedding: new Float32Array([
            0.10000000149011612, 0.20000000298023224, 0.30000001192092896
          ]),
          id: new MediaItemEmbeddingId('test-store', doc1._id.toString()),
          mediaItemId: {
            clientId: '407f1f77bcf86cd799439011',
            objectId: '507f1f77bcf86cd799439011'
          }
        },
        {
          dateTaken: new Date('1970-01-01T00:00:00.000Z'),
          embedding: new Float32Array([
            0.4000000059604645, 0.5, 0.6000000238418579
          ]),
          id: new MediaItemEmbeddingId('test-store', doc2._id.toString()),
          mediaItemId: {
            clientId: '407f1f77bcf86cd799439012',
            objectId: '507f1f77bcf86cd799439012'
          }
        }
      ]);
    });
  });
});
