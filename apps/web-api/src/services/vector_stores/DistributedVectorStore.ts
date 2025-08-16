import {
  BaseVectorStore,
  MediaItemEmbedding,
  MediaItemEmbeddingId,
  MediaItemEmbeddingQueryResult,
  QueryMediaItemEmbeddingRequest
} from './BaseVectorStore';

/** A distributed vector store that joins from other vector stores. */
export class DistributedVectorStore extends BaseVectorStore {
  private stores: BaseVectorStore[];
  private storeIdToStore: Record<string, BaseVectorStore>;

  constructor(stores: BaseVectorStore[]) {
    super();
    this.stores = stores;
    this.storeIdToStore = {};

    for (const store of stores) {
      this.storeIdToStore[store.getStoreId()] = store;
    }
  }

  override getStoreId(): string {
    throw new Error('There is no store ID for this distributed store');
  }

  override async getReleventMediaItemEmbeddings(
    query: QueryMediaItemEmbeddingRequest,
    options?: { abortController?: AbortController }
  ): Promise<MediaItemEmbeddingQueryResult[]> {
    const results = (
      await Promise.all(
        this.stores.map((store) =>
          store.getReleventMediaItemEmbeddings(query, options)
        )
      )
    ).flat();

    return results.sort((a, b) => a.score - b.score).slice(0, query.topK);
  }

  override async getEmbeddingById(
    embeddingId: MediaItemEmbeddingId,
    options?: { abortController?: AbortController }
  ): Promise<MediaItemEmbedding> {
    const store = this.storeIdToStore[embeddingId.vectorStoreId];
    if (!store) {
      throw new Error(`Unable to find embedding ${embeddingId.vectorStoreId}`);
    }
    return store.getEmbeddingById(embeddingId, options);
  }
}
