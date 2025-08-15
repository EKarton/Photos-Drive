import { Injectable } from '@angular/core';
import {
  AutoTokenizer,
  CLIPTextModelWithProjection,
  PreTrainedModel,
  PreTrainedTokenizer,
  ProgressInfo,
  Tensor,
} from '@huggingface/transformers';
import { from, map, Observable, shareReplay, switchMap } from 'rxjs';

export const MODEL_NAME = 'Xenova/clip-vit-large-patch14';

@Injectable({ providedIn: 'root' })
export class OpenClipEmbedderService {
  // Note: the from() function loads the model right away
  private model$: Observable<[PreTrainedTokenizer, PreTrainedModel]> = from(
    Promise.all([
      AutoTokenizer.from_pretrained(MODEL_NAME),
      CLIPTextModelWithProjection.from_pretrained(MODEL_NAME, {
        progress_callback: this.progressCallback,
        cache_dir: './.cache',
        dtype: 'fp32',
      }),
    ]),
  ).pipe(shareReplay({ bufferSize: 1, refCount: true }));

  constructor() {
    this.model$.subscribe(() => console.log('Loaded clip embedder models'));
  }

  private progressCallback(event: ProgressInfo) {
    if (event.status === 'progress') {
      console.log(`Downloading: ${event.file} ${event.progress}%`);
    }
  }

  getTextEmbedding(text: string): Observable<Float32Array> {
    return this.model$.pipe(
      switchMap(([tokenizer, textModel]) => {
        const textInputs = tokenizer(text, {
          padding: true,
          truncation: true,
        });

        return from(textModel(textInputs, {})).pipe(
          map((output: unknown) => {
            const { text_embeds } = output as { text_embeds: Tensor };
            return text_embeds.normalize(2, -1).data as Float32Array;
          }),
        );
      }),
    );
  }
}
