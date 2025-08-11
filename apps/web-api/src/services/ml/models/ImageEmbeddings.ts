export interface ImageEmbedder {
  /**
   * Returns the embeddings of a text.
   *
   * @param text Text to embed
   * @returns the embedding for that text
   */
  embedText(text: string): Promise<Float32Array>;

  /**
   * Returns the embeddings of an image.
   *
   * @param image An image
   * @returns the embedding for that image
   */
  embedImage(imag: Blob): Promise<Float32Array>;
}
