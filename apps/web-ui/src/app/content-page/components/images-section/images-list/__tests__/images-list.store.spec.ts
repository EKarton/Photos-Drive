import { TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { of, throwError } from 'rxjs';

import { authState } from '../../../../../auth/store';
import {
  ListMediaItemsInAlbumResponse,
  MediaItem,
} from '../../../../services/webapi.service';
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
    },
    {
      id: '2',
      fileName: 'cat.png',
      hashCode: 'xyz',
      gPhotosMediaItemId: 'gMediaItem2',
    },
  ];
  const dummyResponse: ListMediaItemsInAlbumResponse = {
    mediaItems: dummyMediaItems,
    nextPageToken: 'next123',
  };

  beforeEach(() => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'listMediaItemsInAlbum',
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
    mockWebApiService.listMediaItemsInAlbum.and.returnValue(of(dummyResponse));

    store.loadInitialPage({ albumId: dummyAlbumId });

    expect(store.mediaItems()).toEqual(dummyMediaItems);
  });

  it('should reset state on failed initial load', () => {
    mockWebApiService.listMediaItemsInAlbum.and.returnValue(
      throwError(() => new Error('API error')),
    );

    store.loadInitialPage({ albumId: dummyAlbumId });

    expect(store.mediaItems()).toEqual([]);
  });

  it('should append media items on load more', () => {
    const firstPage: ListMediaItemsInAlbumResponse = {
      mediaItems: dummyMediaItems,
      nextPageToken: 'next123',
    };

    const secondPage: ListMediaItemsInAlbumResponse = {
      mediaItems: [
        {
          id: '3',
          fileName: 'lizard.png',
          hashCode: 'wasd',
          gPhotosMediaItemId: 'gMediaItem3',
        },
      ],
      nextPageToken: undefined,
    };

    // Set up initial state manually
    mockWebApiService.listMediaItemsInAlbum.and.returnValue(of(firstPage));
    store.loadInitialPage({ albumId: dummyAlbumId });

    mockWebApiService.listMediaItemsInAlbum.and.returnValue(of(secondPage));
    store.loadMoreMediaItems({});

    expect(store.mediaItems()).toEqual([
      ...dummyMediaItems,
      ...secondPage.mediaItems,
    ]);
  });

  it('should handle errors when loading more media items fail', () => {
    const firstPage: ListMediaItemsInAlbumResponse = {
      mediaItems: dummyMediaItems,
      nextPageToken: 'next123',
    };

    // Set up initial state manually
    mockWebApiService.listMediaItemsInAlbum.and.returnValue(of(firstPage));
    store.loadInitialPage({ albumId: dummyAlbumId });

    mockWebApiService.listMediaItemsInAlbum.and.returnValue(
      throwError(() => new Error('API Error')),
    );
    store.loadMoreMediaItems({});

    expect(store.mediaItems()).toEqual([...dummyMediaItems]);
  });

  it('should not load more if already at end of list', () => {
    const firstPage: ListMediaItemsInAlbumResponse = {
      mediaItems: dummyMediaItems,
      nextPageToken: undefined,
    };

    mockWebApiService.listMediaItemsInAlbum.and.returnValue(of(firstPage));
    store.loadInitialPage({ albumId: dummyAlbumId });
    store.loadMoreMediaItems({});

    expect(mockWebApiService.listMediaItemsInAlbum).toHaveBeenCalledTimes(1);
    expect(store.mediaItems()).toEqual(dummyMediaItems);
  });
});
