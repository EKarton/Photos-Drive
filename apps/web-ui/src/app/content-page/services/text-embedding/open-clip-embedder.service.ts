import { inject, Injectable } from '@angular/core';
import {
  AutoTokenizer,
  CLIPTextModelWithProjection,
  PreTrainedModel,
  PreTrainedTokenizer,
  Tensor,
} from '@huggingface/transformers';
import { from, map, Observable, shareReplay, switchMap, tap } from 'rxjs';

import { NAVIGATOR } from '../../../app.tokens';

export const MODEL_NAME = 'Xenova/clip-vit-large-patch14';

@Injectable({ providedIn: 'root' })
export class OpenClipEmbedderService {
  private readonly navigator = inject(NAVIGATOR);

  private model$: Observable<[PreTrainedTokenizer, PreTrainedModel]> = from(
    this.loadModels(),
  ).pipe(
    shareReplay({ bufferSize: 1, refCount: true }),
    tap(() => {
      console.log(`Loaded ${MODEL_NAME}`);
    }),
  );

  private loadModels(): Promise<[PreTrainedTokenizer, PreTrainedModel]> {
    console.log(`Loading ${MODEL_NAME}`);

    const device = this.selectBestDevice();
    console.log('Device:', this.selectBestDevice());

    return Promise.all([
      AutoTokenizer.from_pretrained(MODEL_NAME),
      CLIPTextModelWithProjection.from_pretrained(MODEL_NAME, {
        device,
        dtype: 'fp32',
      }),
    ]);
  }

  private selectBestDevice(): 'webgpu' | 'wasm' {
    return typeof this.navigator !== 'undefined' && 'gpu' in this.navigator
      ? 'webgpu'
      : 'wasm';
  }

  /** Gets the text embeddings for a particular query */
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
