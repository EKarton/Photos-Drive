import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { Store } from '@ngrx/store';
import { of } from 'rxjs';

import {
  toFailure,
  toPending,
  toSuccess,
} from '../../../../../shared/results/results';
import { ListMediaItemsResponse } from '../../../../services/types/list-media-items';
import { MediaItem } from '../../../../services/types/media-item';
import { WebApiService } from '../../../../services/webapi.service';
import {
  DEFAULT_DELAY_BETWEEN_PAGES,
  ImagesMapStore,
  INITIAL_STATE,
} from '../images-map.store';

const MEDIA_ITEM_1: MediaItem = {
  id: 'photos1',
  fileName: 'cat.png',
  hashCode: '',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
  width: 200,
  height: 300,
  location: {
    latitude: -79,
    longitude: 80,
  },
  dateTaken: new Date('2024-05-27T13:17:46.000Z'),
};

const MEDIA_ITEM_2: MediaItem = {
  id: 'photos2',
  fileName: 'dog.png',
  hashCode: '',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem2',
  width: 200,
  height: 300,
  location: {
    latitude: -79,
    longitude: 80.1,
  },
  dateTaken: new Date('2024-05-27T13:17:46.000Z'),
};

describe('ImagesMapStore', () => {
  let store: ImagesMapStore;
  let mockWebApi: jasmine.SpyObj<WebApiService>;
  let mockNgRxStore: jasmine.SpyObj<Store>;

  beforeEach(() => {
    mockWebApi = jasmine.createSpyObj('WebApiService', ['listMediaItems']);
    mockNgRxStore = jasmine.createSpyObj('Store', ['select']);

    TestBed.configureTestingModule({
      providers: [
        ImagesMapStore,
        { provide: WebApiService, useValue: mockWebApi },
        { provide: Store, useValue: mockNgRxStore },
      ],
    });

    store = TestBed.inject(ImagesMapStore);
  });

  it('should initialize with the correct initial state', () => {
    expect(store.state()).toEqual(INITIAL_STATE);
  });

  it('should set isFetchingImages and imagesResult to pending when loadImages is called', fakeAsync(() => {
    mockNgRxStore.select.and.returnValue(of('accessToken'));
    mockWebApi.listMediaItems.and.returnValue(
      of(toPending<ListMediaItemsResponse>()),
    );

    store.loadImages({ albumId: 'album1' });
    tick();

    expect(store.state().isFetchingImages).toBeTrue();
    expect(store.state().imagesResult).toEqual(toPending());
  }));

  it('should fetch images and update state on success', fakeAsync(() => {
    const response: ListMediaItemsResponse = {
      mediaItems: [MEDIA_ITEM_1],
      nextPageToken: undefined,
    };

    mockNgRxStore.select.and.returnValue(of('accessToken'));
    mockWebApi.listMediaItems.and.returnValue(of(toSuccess(response)));

    store.loadImages({ albumId: 'album1' });
    tick();

    expect(store.state().imagesResult).toEqual(toSuccess([MEDIA_ITEM_1]));
    expect(store.state().isFetchingImages).toBeFalse();
  }));

  it('should fetch all pages if nextPageToken is present', fakeAsync(() => {
    const firstPage = {
      mediaItems: [MEDIA_ITEM_1],
      nextPageToken: 'page2',
    };
    const secondPage = {
      mediaItems: [MEDIA_ITEM_2],
      nextPageToken: undefined,
    };

    mockNgRxStore.select.and.returnValue(of('accessToken'));
    mockWebApi.listMediaItems.and.returnValues(
      of(toSuccess(firstPage)),
      of(toSuccess(secondPage)),
    );

    store.loadImages({ albumId: 'album1' });
    tick(DEFAULT_DELAY_BETWEEN_PAGES + 1);

    expect(store.state().imagesResult).toEqual(
      toSuccess([MEDIA_ITEM_1, MEDIA_ITEM_2]),
    );
    expect(store.state().isFetchingImages).toBeFalse();
  }));

  it('should handle errors and not update imagesResult on error', fakeAsync(() => {
    const error = new Error('Random error');

    mockNgRxStore.select.and.returnValue(of('accessToken'));
    mockWebApi.listMediaItems.and.returnValue(
      of(toFailure<ListMediaItemsResponse>(error)),
    );

    store.loadImages({ albumId: 'album1' });
    tick();

    expect(store.state().imagesResult).toEqual(toFailure(error));
    expect(store.state().isFetchingImages).toBeTrue();
  }));

  it('should use delayBetweenPages if provided', fakeAsync(() => {
    const firstPage = {
      mediaItems: [MEDIA_ITEM_1 as MediaItem],
      nextPageToken: 'page2',
    };
    const secondPage = {
      mediaItems: [MEDIA_ITEM_2 as MediaItem],
      nextPageToken: undefined,
    };

    mockNgRxStore.select.and.returnValue(of('accessToken'));
    mockWebApi.listMediaItems.and.returnValues(
      of(toSuccess(firstPage)),
      of(toSuccess(secondPage)),
    );

    const customDelay = 200;
    store.loadImages({ albumId: 'album1', delayBetweenPages: customDelay });

    // First call
    tick();
    // Wait for custom delay
    tick(customDelay + 1);

    expect(store.state().imagesResult).toEqual(
      toSuccess([MEDIA_ITEM_1, MEDIA_ITEM_2]),
    );
    expect(store.state().isFetchingImages).toBeFalse();
  }));
});
