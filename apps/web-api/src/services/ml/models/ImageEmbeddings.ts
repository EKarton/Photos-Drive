export interface ImageEmbedder {
  /**
   * Returns the embeddings of texts.
   *
   * @param texts A list of texts
   * @returns a list of embeddings for each text
   */
  embedTexts(texts: string[]): Promise<Float32Array[]>;

  /**
   * Returns the embeddings of images.
   *
   * @param images A list of images
   * @returns a list of embeddings for each image
   */
  embedImages(images: Blob[]): Promise<Float32Array[]>;
}
