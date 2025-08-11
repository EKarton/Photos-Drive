import {
  AutoProcessor,
  AutoTokenizer,
  CLIPTextModelWithProjection,
  CLIPVisionModelWithProjection,
  PreTrainedModel,
  PreTrainedTokenizer,
  Processor,
  ProgressInfo,
  RawImage,
  Tensor
} from '@huggingface/transformers';
import * as tf from '@tensorflow/tfjs';
import { ImageEmbedder } from './ImageEmbeddings';

export class OpenCLIPImageEmbedder implements ImageEmbedder {
  private processor?: Processor;
  private visionModel?: PreTrainedModel;
  private tokenizer?: PreTrainedTokenizer;
  private textModel?: PreTrainedModel;

  constructor(public modelName = 'Xenova/clip-vit-large-patch14') {}

  async initialize() {
    this.processor = await AutoProcessor.from_pretrained(this.modelName);
    this.visionModel = await CLIPVisionModelWithProjection.from_pretrained(
      this.modelName,
      { progress_callback: this.progress_callback, cache_dir: './.cache' }
    );
    this.tokenizer = await AutoTokenizer.from_pretrained(this.modelName);
    this.textModel = await CLIPTextModelWithProjection.from_pretrained(
      this.modelName,
      { progress_callback: this.progress_callback, cache_dir: './.cache' }
    );
  }

  private progress_callback(event: ProgressInfo) {
    if (event.status === 'progress') {
      console.log(`Downloading: ${event.file} ${event.progress}%`);
    }
  }

  async embedTexts(texts: string[]): Promise<Float32Array[]> {
    const textInputs = this.tokenizer!(texts, {
      padding: true,
      truncation: true
    });
    const output = await this.textModel!(textInputs);
    const textEmbeddings: Tensor = output.text_embeds;
    return this.hehe(textEmbeddings.normalize(2, -1));
  }

  async embedImages(images: Blob[]): Promise<Float32Array[]> {
    const rawImages = await Promise.all(
      images.map(async (img) => await RawImage.read(img))
    );
    const imageInputs = await this.processor!(rawImages);
    const output = await this.visionModel!(imageInputs);
    const imageEmbeddings: Tensor = output.image_embeds;
    return this.hehe(imageEmbeddings.normalize(2, -1));
  }

  private hehe(tensor: Tensor): Float32Array[] {
    const float32Data: Float32Array = tensor.data;
    const shape = tensor.dims; // e.g., [batchSize, embeddingDim]

    // Now float32Data is a Float32Array of length = batchSize * embeddingDim
    console.log(float32Data.length); // batchSize * embeddingDim

    // If you want to split it into per-item arrays:
    const batchSize = shape[0];
    const embeddingDim = shape[1];
    const embeddingsPerItem: Float32Array[] = [];
    for (let i = 0; i < batchSize; i++) {
      const start = i * embeddingDim;
      const end = start + embeddingDim;
      embeddingsPerItem.push(float32Data.slice(start, end));
    }

    return embeddingsPerItem;
  }
}
