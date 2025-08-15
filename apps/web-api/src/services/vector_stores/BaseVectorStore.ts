import { MediaItemId } from '../metadata_store/MediaItems';

export class MediaItemEmbeddingId {
  readonly vectorStoreId: string;
  readonly objectId: string;

  constructor(vectorStoreId: string, objectId: string) {
    this.vectorStoreId = vectorStoreId;
    this.objectId = objectId;
  }

  static parse(value: string): MediaItemEmbeddingId {
    const [vectorStoreId, objectId] = value.split(':');
    return new MediaItemEmbeddingId(vectorStoreId, objectId);
  }

  toString(): string {
    return `${this.vectorStoreId}:${this.objectId}`;
  }
}

export interface MediaItemEmbedding {
  readonly id: MediaItemEmbeddingId;
  readonly embedding: Float32Array;
  readonly mediaItemId: MediaItemId;
  readonly dateTaken: Date;
}

export interface QueryMediaItemEmbeddingRequest {
  readonly embedding: Float32Array;
  readonly startDateTaken?: Date;
  readonly endDateTaken?: Date;
  readonly withinMediaItemIds?: MediaItemId[];
  readonly topK: number;
}

export abstract class BaseVectorStore {
  abstract getStoreId(): string;

  abstract getReleventMediaItemEmbeddings(
    query: QueryMediaItemEmbeddingRequest,
    options?: { abortController?: AbortController }
  ): Promise<MediaItemEmbedding[]>;

  abstract getEmbeddingById(
    embeddingId: MediaItemEmbeddingId,
    options?: { abortController?: AbortController }
  ): Promise<MediaItemEmbedding>;
}
