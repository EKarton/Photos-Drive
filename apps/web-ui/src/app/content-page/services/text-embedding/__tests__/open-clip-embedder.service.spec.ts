import { TestBed } from '@angular/core/testing';
import * as hf from '@huggingface/transformers';

import { NAVIGATOR } from '../../../../app.tokens';
import { OpenClipEmbedderService } from '../open-clip-embedder.service';

describe('OpenClipEmbedderService', () => {
  beforeEach(() => {
    const mockTokenizer = jasmine
      .createSpyObj('hf.PreTrainedTokenizer', ['_call'])
      ._call.and.returnValue(undefined);

    const mockTextModel = jasmine
      .createSpyObj('hf.PreTrainedModel', ['_call'])
      ._call.and.returnValue(
        Promise.resolve({
          text_embeds: {
            normalize: () => ({
              data: new Float32Array([0.1, 0.2, 0.3]),
            }),
          },
        }),
      );

    spyOn(hf.AutoTokenizer, 'from_pretrained').and.returnValue(
      Promise.resolve(mockTokenizer),
    );
    spyOn(hf.CLIPTextModelWithProjection, 'from_pretrained').and.returnValue(
      Promise.resolve(mockTextModel),
    );
  });

  it('should return normalized text embedding', (done) => {
    TestBed.configureTestingModule({
      providers: [
        OpenClipEmbedderService,
        { provide: NAVIGATOR, useFactory: () => ({}) },
      ],
    });
    const service = TestBed.inject(OpenClipEmbedderService);

    service.getTextEmbedding('test').subscribe((embedding) => {
      expect(embedding).toEqual(new Float32Array([0.1, 0.2, 0.3]));
      done();
    });
  });

  it('should select WebGPU if available', async () => {
    TestBed.configureTestingModule({
      providers: [
        OpenClipEmbedderService,
        { provide: NAVIGATOR, useFactory: () => ({ gpu: true }) },
      ],
    });
    TestBed.inject(OpenClipEmbedderService);

    expect(hf.CLIPTextModelWithProjection.from_pretrained).toHaveBeenCalledWith(
      'Xenova/clip-vit-large-patch14',
      { device: 'webgpu', dtype: 'fp32' },
    );
  });

  it('should select wasm if no gpu is available', async () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: NAVIGATOR,
          useFactory: () => undefined,
        },
        OpenClipEmbedderService,
      ],
    });
    TestBed.inject(OpenClipEmbedderService);

    expect(hf.CLIPTextModelWithProjection.from_pretrained).toHaveBeenCalledWith(
      'Xenova/clip-vit-large-patch14',
      { device: 'wasm', dtype: 'fp32' },
    );
  });
});
