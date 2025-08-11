import {
  AutoTokenizer,
  CLIPTextModelWithProjection,
  PreTrainedModel,
  PreTrainedTokenizer,
  ProgressInfo,
  Tensor
} from '@huggingface/transformers';
import { ImageEmbedder } from './ImageEmbeddings';

export class OpenCLIPImageEmbedder implements ImageEmbedder {
  private tokenizer?: PreTrainedTokenizer;
  private textModel?: PreTrainedModel;

  constructor(public modelName = 'Xenova/clip-vit-large-patch14') {}

  async initialize() {
    const [tokenizer, textModel] = await Promise.all([
      AutoTokenizer.from_pretrained(this.modelName),
      CLIPTextModelWithProjection.from_pretrained(this.modelName, {
        progress_callback: this.progress_callback,
        cache_dir: './.cache',
        dtype: 'fp32'
      })
    ]);

    this.tokenizer = tokenizer;
    this.textModel = textModel;
  }

  async dispose() {
    await this.textModel!.dispose();
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
}
