import { OpenCLIPImageEmbedder } from '../../../../src/services/ml/models/OpenCLIPImageEmbeddings';

describe('OpenCLIPImageEmbedder (integration test with real model)', () => {
  jest.setTimeout(60000); // 60 seconds timeout

  let embedder: OpenCLIPImageEmbedder;

  beforeAll(async () => {
    embedder = new OpenCLIPImageEmbedder();
    await embedder.initialize();
  }, 60000);

  afterAll(async () => {
    await embedder.dispose();
  }, 60000);

  it('generates a real embedding vector for text', async () => {
    const text = 'A photo of a cat';
    const embedding = await embedder.embedText(text);

    expect(embedding).toBeInstanceOf(Float32Array);
    expect(embedding.length).toEqual(768);

    // Optional: basic sanity check — embeddings should be normalized
    const norm = Math.sqrt(embedding.reduce((acc, v) => acc + v * v, 0));
    expect(norm).toBeCloseTo(1.0, 5);
  });
});
