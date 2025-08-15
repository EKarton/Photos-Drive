import { MediaItemEmbeddingId } from '../../../src/services/vector_stores/BaseVectorStore';

describe('MediaItemEmbeddingId', () => {
  it('constructor sets vectorStoreId and objectId', () => {
    const id = new MediaItemEmbeddingId('store123', 'obj456');

    expect(id.vectorStoreId).toBe('store123');
    expect(id.objectId).toBe('obj456');
  });

  it('toString returns correct format', () => {
    const id = new MediaItemEmbeddingId('myStore', 'abcdef');

    expect(id.toString()).toBe('myStore:abcdef');
  });

  it('parse creates correct object from string', () => {
    const str = 'storeX:objectY';
    const parsed = MediaItemEmbeddingId.parse(str);

    expect(parsed.vectorStoreId).toBe('storeX');
    expect(parsed.objectId).toBe('objectY');
  });
});
