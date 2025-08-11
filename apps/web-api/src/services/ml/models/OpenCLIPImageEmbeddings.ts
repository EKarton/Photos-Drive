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
import { ImageEmbedder } from './ImageEmbeddings';

export class OpenCLIPImageEmbedder implements ImageEmbedder {
  private processor?: Processor;
  private visionModel?: PreTrainedModel;
  private tokenizer?: PreTrainedTokenizer;
  private textModel?: PreTrainedModel;

  constructor(public modelName = 'Xenova/clip-vit-large-patch14') {}

  async initialize() {
    const [processor, visionModel, tokenizer, textModel] = await Promise.all([
      AutoProcessor.from_pretrained(this.modelName),
      CLIPVisionModelWithProjection.from_pretrained(this.modelName, {
        progress_callback: this.progress_callback,
        cache_dir: './.cache'
      }),
      AutoTokenizer.from_pretrained(this.modelName),
      CLIPTextModelWithProjection.from_pretrained(this.modelName, {
        progress_callback: this.progress_callback,
        cache_dir: './.cache'
      })
    ]);

    this.processor = processor;
    this.visionModel = visionModel;
    this.tokenizer = tokenizer;
    this.textModel = textModel;
  }

  private progress_callback(event: ProgressInfo) {
    if (event.status === 'progress') {
      console.log(`Downloading: ${event.file} ${event.progress}%`);
    }
  }

  async embedText(text: string): Promise<Float32Array> {
    const textInputs = this.tokenizer!(text, {
      padding: true,
      truncation: true
    });
    const output = await this.textModel!(textInputs, {});
    const textEmbeddings: Tensor = output.text_embeds;
    return textEmbeddings.normalize(2, -1).data as Float32Array;
  }

  async embedImage(image: Blob): Promise<Float32Array> {
    const rawImages = await RawImage.read(image);
    const imageInputs = await this.processor!(rawImages);
    const output = await this.visionModel!(imageInputs);
    const imageEmbeddings: Tensor = output.image_embeds;
    return imageEmbeddings.normalize(2, -1).data as Float32Array;
  }
}
