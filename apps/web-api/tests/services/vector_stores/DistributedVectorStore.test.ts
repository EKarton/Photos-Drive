import { jest } from '@jest/globals';
import {
  BaseVectorStore,
  MediaItemEmbeddingId,
  QueryMediaItemEmbeddingRequest
} from '../../../src/services/vector_stores/BaseVectorStore';
import { DistributedVectorStore } from '../../../src/services/vector_stores/DistributedVectorStore';

class FakeVectorStore implements BaseVectorStore {
  constructor(private readonly storeId: string) {}

  public getStoreId(): string {
    return this.storeId;
  }

  public getReleventMediaItemEmbeddings =
    jest.fn<BaseVectorStore['getReleventMediaItemEmbeddings']>();

  public getEmbeddingById = jest.fn<BaseVectorStore['getEmbeddingById']>();
}

describe('DistributedVectorStore', () => {
  let stores: FakeVectorStore[];
  let distributedStore: DistributedVectorStore;

  const mockStore1Id = 'store-1';
  const mockStore2Id = 'store-2';

  const mockResult1 = {
    id: new MediaItemEmbeddingId(mockStore1Id, 'id1'),
    mediaItemId: { clientId: 'client1', objectId: 'obj1' },
    score: 0.95
  };
  const mockResult2 = {
    id: new MediaItemEmbeddingId(mockStore1Id, 'id2'),
    mediaItemId: { clientId: 'client1', objectId: 'obj2' },
    score: 0.92
  };
  const mockResult3 = {
    id: new MediaItemEmbeddingId(mockStore2Id, 'id3'),
    mediaItemId: { clientId: 'client2', objectId: 'obj3' },
    score: 0.98
  };
  const mockResult4 = {
    id: new MediaItemEmbeddingId(mockStore2Id, 'id4'),
    mediaItemId: { clientId: 'client2', objectId: 'obj4' },
    score: 0.88
  };

  beforeAll(() => {
    // Create instances of our fake stores
    stores = [
      new FakeVectorStore(mockStore1Id),
      new FakeVectorStore(mockStore2Id)
    ];
    distributedStore = new DistributedVectorStore(stores);
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('getStoreId should throw an error', () => {
    expect(() => distributedStore.getStoreId()).toThrow(
      'There is no store ID for this distributed store'
    );
  });

  describe('getReleventMediaItemEmbeddings', () => {
    it('should call getReleventMediaItemEmbeddings on all sub-stores and combine results in descending order', async () => {
      // Configure the fake stores to return specific data
      stores[0].getReleventMediaItemEmbeddings.mockResolvedValue([
        mockResult1,
        mockResult2
      ]);
      stores[1].getReleventMediaItemEmbeddings.mockResolvedValue([
        mockResult3,
        mockResult4
      ]);

      const query: QueryMediaItemEmbeddingRequest = {
        embedding: new Float32Array([1, 2, 3]),
        topK: 3
      };
      const results =
        await distributedStore.getReleventMediaItemEmbeddings(query);

      // Verify calls to fakes
      expect(stores[0].getReleventMediaItemEmbeddings).toHaveBeenCalledWith(
        query,
        undefined
      );
      expect(stores[1].getReleventMediaItemEmbeddings).toHaveBeenCalledWith(
        query,
        undefined
      );

      // Verify the combined and sorted results
      expect(results).toEqual([mockResult3, mockResult1, mockResult2]);
      expect(results).toHaveLength(3);
    });

    it('should handle one store rejecting a promise', async () => {
      stores[0].getReleventMediaItemEmbeddings.mockResolvedValue([mockResult1]);
      stores[1].getReleventMediaItemEmbeddings.mockRejectedValue(
        new Error('Network error')
      );

      const query: QueryMediaItemEmbeddingRequest = {
        embedding: new Float32Array([1, 2, 3]),
        topK: 2
      };

      // Ensure Promise.all rejects when one of the promises rejects
      await expect(
        distributedStore.getReleventMediaItemEmbeddings(query)
      ).rejects.toThrow('Network error');
    });
  });

  describe('getEmbeddingById', () => {
    it('should call getEmbeddingById on the correct sub-store', async () => {
      const mockEmbedding = {
        id: new MediaItemEmbeddingId(mockStore1Id, 'existingId'),
        mediaItemId: { clientId: 'client1', objectId: 'obj1' }
      };

      // Configure the correct fake store to return a value
      stores[0].getEmbeddingById.mockResolvedValue(mockEmbedding);
      // Configure the other fake store to return nothing
      stores[1].getEmbeddingById.mockResolvedValue(null);

      const embeddingId = new MediaItemEmbeddingId(mockStore1Id, 'existingId');
      const result = await distributedStore.getEmbeddingById(embeddingId);

      // Assert that the correct fake store was called and the other was not
      expect(stores[0].getEmbeddingById).toHaveBeenCalledWith(
        embeddingId,
        undefined
      );
      expect(stores[1].getEmbeddingById).not.toHaveBeenCalled();
      expect(result).toEqual(mockEmbedding);
    });

    it('should throw an error if the store is not found', async () => {
      const embeddingId = new MediaItemEmbeddingId('non-existent-store', 'id');
      await expect(
        distributedStore.getEmbeddingById(embeddingId)
      ).rejects.toThrow('Unable to find embedding non-existent-store');
    });
  });
});
