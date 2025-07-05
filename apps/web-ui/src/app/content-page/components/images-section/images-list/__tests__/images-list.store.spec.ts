import { TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { authState } from '../../../../../auth/store';
import { toFailure, toSuccess } from '../../../../../shared/results/results';
import { ListMediaItemsResponse } from '../../../../services/list-media-items';
import { MediaItem } from '../../../../services/media-items';
import { WebApiService } from '../../../../services/webapi.service';
import { ImagesListStore } from '../images-list.store';

describe('ImagesListStore', () => {
  let store: ImagesListStore;
  let mockWebApiService: jasmine.SpyObj<WebApiService>;

  const dummyToken = 'mock-token';
  const dummyAlbumId = 'album123';
  const dummyMediaItems: MediaItem[] = [
    {
      id: '1',
      fileName: 'dog.png',
      hashCode: '123',
      gPhotosMediaItemId: 'gMediaItem1',
      width: 200,
      height: 300,
      dateTaken: new Date('2024-05-27T13:17:46.000Z'),
    },
    {
      id: '2',
      fileName: 'cat.png',
      hashCode: 'xyz',
      gPhotosMediaItemId: 'gMediaItem2',
      width: 200,
      height: 300,
      dateTaken: new Date('2024-05-27T13:17:46.000Z'),
    },
  ];
  const dummyResponse: ListMediaItemsResponse = {
    mediaItems: dummyMediaItems,
    nextPageToken: 'next123',
  };

  beforeEach(() => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'listMediaItems',
    ]);

    TestBed.configureTestingModule({
      providers: [
        ImagesListStore,
        { provide: WebApiService, useValue: mockWebApiService },
        provideMockStore({
          selectors: [
            {
              selector: authState.selectAuthToken,
              value: dummyToken,
            },
          ],
        }),
      ],
    });

    store = TestBed.inject(ImagesListStore);
  });

  it('should load initial page successfully', () => {
    mockWebApiService.listMediaItems.and.returnValue(
      of(toSuccess(dummyResponse)),
    );

    store.loadInitialPage({ albumId: dummyAlbumId });

    expect(store.mediaItems()).toEqual(dummyMediaItems);
  });

  it('should reset state on failed initial load', () => {
    mockWebApiService.listMediaItems.and.returnValue(
      of(toFailure<ListMediaItemsResponse>(new Error('API error'))),
    );

    store.loadInitialPage({ albumId: dummyAlbumId });

    expect(store.mediaItems()).toEqual([]);
  });

  it('should append media items on load more', () => {
    const firstPage: ListMediaItemsResponse = {
      mediaItems: dummyMediaItems,
      nextPageToken: 'next123',
    };

    const secondPage: ListMediaItemsResponse = {
      mediaItems: [
        {
          id: '3',
          fileName: 'lizard.png',
          hashCode: 'wasd',
          gPhotosMediaItemId: 'gMediaItem3',
          width: 200,
          height: 300,
          dateTaken: new Date('2024-05-27T13:17:46.000Z'),
        },
      ],
      nextPageToken: undefined,
    };

    // Set up initial state manually
    mockWebApiService.listMediaItems.and.returnValue(of(toSuccess(firstPage)));
    store.loadInitialPage({ albumId: dummyAlbumId });

    mockWebApiService.listMediaItems.and.returnValue(of(toSuccess(secondPage)));
    store.loadMoreMediaItems({});

    expect(store.mediaItems()).toEqual([
      ...dummyMediaItems,
      ...secondPage.mediaItems,
    ]);
  });

  it('should handle errors when loading more media items fail', () => {
    const firstPage: ListMediaItemsResponse = {
      mediaItems: dummyMediaItems,
      nextPageToken: 'next123',
    };

    // Set up initial state manually
    mockWebApiService.listMediaItems.and.returnValue(of(toSuccess(firstPage)));
    store.loadInitialPage({ albumId: dummyAlbumId });

    mockWebApiService.listMediaItems.and.returnValue(
      of(toFailure<ListMediaItemsResponse>(new Error('API Error'))),
    );
    store.loadMoreMediaItems({});

    expect(store.mediaItems()).toEqual([...dummyMediaItems]);
  });

  it('should not load more if already at end of list', () => {
    const firstPage: ListMediaItemsResponse = {
      mediaItems: dummyMediaItems,
      nextPageToken: undefined,
    };

    mockWebApiService.listMediaItems.and.returnValue(of(toSuccess(firstPage)));
    store.loadInitialPage({ albumId: dummyAlbumId });
    store.loadMoreMediaItems({});

    expect(mockWebApiService.listMediaItems).toHaveBeenCalledTimes(1);
    expect(store.mediaItems()).toEqual(dummyMediaItems);
  });
});
