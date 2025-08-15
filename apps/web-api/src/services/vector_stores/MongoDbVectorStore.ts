import {
  Binary,
  Collection,
  Filter,
  MongoClient,
  Document as MongoDBDocument,
  ObjectId
} from 'mongodb';
import { convertStringToMediaItemId } from '../metadata_store/MediaItems';
import {
  BaseVectorStore,
  MediaItemEmbedding,
  MediaItemEmbeddingId,
  QueryMediaItemEmbeddingRequest
} from './BaseVectorStore';

const EMBEDDING_INDEX_NAME = 'vector_index';

export class MongoDbVectorStore extends BaseVectorStore {
  private readonly _storeId: string;
  private readonly _collection: Collection;
  private readonly _embeddingIndexName: string;

  constructor(
    storeId: string,
    mongoClient: MongoClient,
    dbName: string,
    collectionName: string,
    embeddingIndexName = EMBEDDING_INDEX_NAME
  ) {
    super();
    this._storeId = storeId;
    this._collection = mongoClient.db(dbName).collection(collectionName);
    this._embeddingIndexName = embeddingIndexName;
  }

  override getStoreId(): string {
    return this._storeId;
  }

  override async getEmbeddingById(
    id: MediaItemEmbeddingId,
    options?: { abortController?: AbortController }
  ): Promise<MediaItemEmbedding> {
    const doc = await this._collection.findOne(
      {
        _id: new ObjectId(id.objectId)
      },
      { signal: options?.abortController?.signal }
    );

    if (!doc) {
      throw new Error(`Cannot find embedding for id ${id.toString()}`);
    }

    return this.parseDocumentToMediaItemEmbedding(doc);
  }

  override async getReleventMediaItemEmbeddings(
    query: QueryMediaItemEmbeddingRequest,
    options?: { abortController?: AbortController }
  ): Promise<MediaItemEmbedding[]> {
    const filter: Filter<MongoDBDocument> = {};

    if (query.startDateTaken || query.endDateTaken) {
      filter.date_taken = {};
      if (query.startDateTaken) {
        filter.date_taken.$gte = query.startDateTaken;
      }
      if (query.endDateTaken) {
        filter.date_taken.$lte = query.endDateTaken;
      }
    }

    if (query.withinMediaItemIds && query.withinMediaItemIds.length > 0) {
      filter.media_item_id = {
        $in: query.withinMediaItemIds
      };
    }

    const pipeline = [
      {
        $vectorSearch: {
          index: this._embeddingIndexName,
          path: 'embedding',
          queryVector: this.toMongoVector(query.embedding),
          numCandidates: query.topK * 5,
          filter,
          limit: query.topK
        }
      }
    ];

    const cursor = this._collection.aggregate(pipeline, {
      signal: options?.abortController?.signal
    });
    const results: MediaItemEmbedding[] = [];
    for await (const doc of cursor) {
      results.push(this.parseDocumentToMediaItemEmbedding(doc));
    }
    return results;
  }

  // Helper to parse raw document to MediaItemEmbedding
  private parseDocumentToMediaItemEmbedding(
    doc: MongoDBDocument
  ): MediaItemEmbedding {
    const id = new MediaItemEmbeddingId(this._storeId, doc._id.toHexString());
    const embedding = this.parseMongoVector(doc.embedding);
    const mediaItemId = convertStringToMediaItemId(doc.media_item_id);
    const dateTaken = doc.date_taken ? new Date(doc.date_taken) : new Date(0);

    return {
      id,
      embedding,
      mediaItemId,
      dateTaken
    };
  }

  private toMongoVector(embedding: Float32Array): Binary {
    return Binary.fromFloat32Array(embedding);
  }

  private parseMongoVector(binary: Binary): Float32Array {
    return binary.toFloat32Array();
  }
}
