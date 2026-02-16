import { TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { authState } from '../../../../../../auth/store';
import {
  toFailure,
  toPending,
  toSuccess,
} from '../../../../../../shared/results/results';
import { GetMediaItemImageResponse } from '../../../../../services/web-api/types/get-media-item-image';
import { WebApiService } from '../../../../../services/web-api/web-api.service';
import { ImageMapMarkerStore, INITIAL_STATE } from '../image-map-marker.store';

const MEDIA_ITEM_ID = 'client1:photos1';

const MEDIA_ITEM_IMAGE_URL = 'http://www.google.com/photos/1';

describe('ImageMapMarkerStore', () => {
  let store: ImageMapMarkerStore;
  let webApiService: jasmine.SpyObj<WebApiService>;

  const fakeAuthToken = 'auth-token';

  beforeEach(() => {
    const webApiServiceSpy = jasmine.createSpyObj('WebApiService', [
      'getMediaItemImage',
    ]);

    TestBed.configureTestingModule({
      providers: [
        ImageMapMarkerStore,
        provideMockStore({
          selectors: [
            {
              selector: authState.selectAuthToken,
              value: fakeAuthToken,
            },
          ],
        }),
        { provide: WebApiService, useValue: webApiServiceSpy },
      ],
    });

    store = TestBed.inject(ImageMapMarkerStore);
    webApiService = TestBed.inject(
      WebApiService,
    ) as jasmine.SpyObj<WebApiService>;
  });

  it('should initialize with pending state', () => {
    webApiService.getMediaItemImage.and.returnValue(
      of(toPending<GetMediaItemImageResponse>()),
    );

    expect(store.url()).toEqual(INITIAL_STATE.url);
  });

  it('should load and update state on success', () => {
    webApiService.getMediaItemImage.and.returnValue(
      of(toSuccess({ url: MEDIA_ITEM_IMAGE_URL })),
    );

    store.loadUrl(MEDIA_ITEM_ID);

    expect(webApiService.getMediaItemImage).toHaveBeenCalledWith(
      fakeAuthToken,
      MEDIA_ITEM_ID,
    );
    expect(store.url()).toEqual(toSuccess(MEDIA_ITEM_IMAGE_URL));
  });

  it('should update state to failure on API error', () => {
    const error = new Error('API failed');
    webApiService.getMediaItemImage.and.returnValue(
      of(toFailure<GetMediaItemImageResponse>(error)),
    );

    store.loadUrl(MEDIA_ITEM_ID);

    expect(store.url()).toEqual(toFailure(error));
  });
});
