/** Represents an image + text embedder. */
export interface ImageEmbedder {
  /**
   * Returns the embeddings of a text.
   *
   * @param text Text to embed
   * @returns the embedding for that text
   */
  embedText(text: string): Promise<Float32Array>;
}
