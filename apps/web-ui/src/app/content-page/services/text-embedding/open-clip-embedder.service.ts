import { Injectable } from '@angular/core';
import {
  AutoTokenizer,
  CLIPTextModelWithProjection,
  PreTrainedModel,
  PreTrainedTokenizer,
  ProgressInfo,
  Tensor,
} from '@huggingface/transformers';
import { from, map, Observable, shareReplay, switchMap, tap } from 'rxjs';

export const MODEL_NAME = 'Xenova/clip-vit-large-patch14';

@Injectable({ providedIn: 'root' })
export class OpenClipEmbedderService {
  // Note: the from() function loads the model right away
  private model$: Observable<[PreTrainedTokenizer, PreTrainedModel]> = from(
    loadModels(),
  ).pipe(
    shareReplay({ bufferSize: 1, refCount: true }),
    tap(() => {
      console.log('Loaded models');
    }),
  );

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

function loadModels(): Promise<[PreTrainedTokenizer, PreTrainedModel]> {
  console.log(`Loading ${MODEL_NAME}`);

  const device = selectBestDevice();
  console.log('Device:', selectBestDevice());

  return Promise.all([
    AutoTokenizer.from_pretrained(MODEL_NAME),
    CLIPTextModelWithProjection.from_pretrained(MODEL_NAME, {
      progress_callback: progressCallback,
      device,
      dtype: 'fp32',
    }),
  ]);
}

function progressCallback(event: ProgressInfo) {
  if (event.status === 'progress') {
    console.log(`Downloading: ${event.file} ${event.progress}%`);
  }
}

function selectBestDevice(): 'webgpu' | 'wasm' {
  // WebGPU requires a secure context (https or localhost) and browser support
  if (typeof navigator !== 'undefined' && 'gpu' in navigator) {
    return 'webgpu';
  }
  return 'wasm'; // CPU backend
}
