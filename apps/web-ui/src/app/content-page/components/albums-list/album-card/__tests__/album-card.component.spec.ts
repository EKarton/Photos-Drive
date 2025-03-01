import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { toFailure, toSuccess } from '../../../../../shared/results/results';
import {
  Album,
  GPhotosMediaItem,
  MediaItem,
} from '../../../../services/webapi.service';
import { albumsState } from '../../../../store/albums';
import { gPhotosMediaItemsState } from '../../../../store/gphoto-media-items';
import { mediaItemsState } from '../../../../store/media-items';
import { AlbumCardComponent } from '../album-card.component';

const ALBUM_DETAILS_1: Album = {
  id: 'album3',
  albumName: 'Photos',
  parentAlbumId: 'album2',
  childAlbumIds: [],
  mediaItemIds: ['photos1'],
};

const MEDIA_ITEM_DETAILS_PHOTOS_1: MediaItem = {
  id: 'photos1',
  fileName: 'cat.png',
  hashCode: '',
  gPhotosClientId: 'gPhotosClient1',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
};

const G_MEDIA_ITEM_DETAILS_PHOTO_1: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/photos/1',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: '4032',
    height: '3024',
  },
};

describe('AlbumCardComponent', () => {
  let store: MockStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlbumCardComponent],
      providers: [
        provideMockStore({
          initialState: {
            [albumsState.FEATURE_KEY]: albumsState.buildInitialState(),
            [mediaItemsState.FEATURE_KEY]: mediaItemsState.buildInitialState(),
            [gPhotosMediaItemsState.FEATURE_KEY]:
              gPhotosMediaItemsState.buildInitialState(),
          },
        }),
        provideRouter([]),
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    spyOn(store, 'dispatch');
  });

  it('should render skeleton when media item is not loaded yet', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="album-image-skeleton"]',
    );
    expect(spinner).toBeTruthy();
  });

  it('should show error when media item has failed to load', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set('album3', toSuccess(ALBUM_DETAILS_1)),
      },
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'photos1',
          toFailure(new Error('Random error')),
        ),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]:
        gPhotosMediaItemsState.buildInitialState(),
    });
    store.refreshState();
    fixture.detectChanges();

    const error = fixture.nativeElement.querySelector(
      '[data-testid="album-image-error"]',
    );
    expect(error).toBeTruthy();
  });

  it('should render image when media item has loaded already', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set('album3', toSuccess(ALBUM_DETAILS_1)),
      },
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'photos1',
          toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_1),
        ),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'gPhotosClient1:gPhotosMediaItem1',
          toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1),
        ),
      },
    });
    store.refreshState();
    fixture.detectChanges();

    const image = fixture.nativeElement.querySelector(
      '[data-testid="album-image"]',
    );
    expect(image.src).toEqual('http://www.google.com/photos/1');
  });

  it('should render template image when gmedia item has no base url', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set('album3', toSuccess(ALBUM_DETAILS_1)),
      },
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'photos1',
          toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_1),
        ),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'gPhotosClient1:gPhotosMediaItem1',
          toSuccess({
            ...G_MEDIA_ITEM_DETAILS_PHOTO_1,
            baseUrl: undefined,
          }),
        ),
      },
    });
    store.refreshState();
    fixture.detectChanges();

    const image = fixture.nativeElement.querySelector(
      '[data-testid="album-image-folder"]',
    );
    expect(image).toBeTruthy();
  });

  it('should render template image when album has no images', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'album3',
          toSuccess({
            ...ALBUM_DETAILS_1,
            mediaItemIds: [],
          }),
        ),
      },
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap(),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap(),
      },
    });
    store.refreshState();
    fixture.detectChanges();

    const image = fixture.nativeElement.querySelector(
      '[data-testid="album-image-folder"]',
    );
    expect(image).toBeTruthy();
  });

  [
    { numPhotos: 10, numAlbums: 10, expectedString: '10 photos · 10 albums' },
    { numPhotos: 1, numAlbums: 10, expectedString: '1 photo · 10 albums' },
    { numPhotos: 10, numAlbums: 1, expectedString: '10 photos · 1 album' },
    { numPhotos: 0, numAlbums: 10, expectedString: '10 albums' },
    { numPhotos: 10, numAlbums: 0, expectedString: '10 photos' },
    { numPhotos: 0, numAlbums: 1, expectedString: '1 album' },
    { numPhotos: 1, numAlbums: 0, expectedString: '1 photo' },
  ].forEach(({ numPhotos, numAlbums, expectedString }) => {
    it(`should render component correctly given num photos = ${numPhotos} and num child albums = ${numAlbums}`, () => {
      const apiResponse: Album = {
        id: 'album3',
        albumName: 'Photos',
        parentAlbumId: 'album2',
        childAlbumIds: Array.from({ length: numAlbums }, (i) => `c-${i}`),
        mediaItemIds: Array.from({ length: numPhotos }, (i) => `m-${i}`),
      };
      store.setState({
        [albumsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap().set('album3', toSuccess(apiResponse)),
        },
        [mediaItemsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap().set(
            'photos1',
            toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_1),
          ),
        },
        [gPhotosMediaItemsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap().set(
            'gPhotosClient1:gPhotosMediaItem1',
            toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1),
          ),
        },
      });
      store.refreshState();

      const fixture = TestBed.createComponent(AlbumCardComponent);
      fixture.componentRef.setInput('albumId', 'album3');
      fixture.detectChanges();

      const element = fixture.nativeElement.querySelector(
        '.album-card__sub-text',
      );
      expect(element.textContent).toContain(expectedString);
      const component = fixture.componentInstance;
      expect(component).toBeTruthy();
    });
  });

  it('should render spinner given no response', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.skeleton')).toBeTruthy();
  });
});
