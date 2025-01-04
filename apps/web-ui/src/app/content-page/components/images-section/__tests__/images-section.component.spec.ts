import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { WINDOW } from '../../../../app.tokens';
import { toSuccess } from '../../../../shared/results/results';
import { GPhotosMediaItemDetails } from '../../../services/gphotos-api.service';
import { Album, MediaItem } from '../../../services/webapi.service';
import { albumsActions, albumsState } from '../../../store/albums';
import {
  gPhotosMediaItemsActions,
  gPhotosMediaItemsState,
} from '../../../store/gphoto-media-items';
import { mediaItemsActions, mediaItemsState } from '../../../store/media-items';
import {
  mediaViewerActions,
  mediaViewerState,
} from '../../../store/media-viewer';
import { ImagesSectionComponent } from '../images-section.component';

const ALBUM_DETAILS_PHOTOS: Album = {
  id: 'album3',
  albumName: 'Photos',
  parentAlbumId: 'album2',
  childAlbumIds: ['album4', 'album5'],
  mediaItemIds: ['photos1', 'photos2'],
};

const MEDIA_ITEM_DETAILS_PHOTOS_1: MediaItem = {
  id: 'photos1',
  fileName: 'dog.png',
  hashCode: '',
  gPhotosClientId: 'gPhotosClient1',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
};

const MEDIA_ITEM_DETAILS_PHOTOS_2: MediaItem = {
  id: 'photos2',
  fileName: 'cat.png',
  hashCode: '',
  gPhotosClientId: 'gPhotosClient1',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem2',
};

const G_MEDIA_ITEM_DETAILS_PHOTO_1: GPhotosMediaItemDetails = {
  id: 'gPhotosMediaItem1',
  description: '',
  productUrl: '',
  baseUrl: 'http://www.google.com/photos/1',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: 200,
    height: 200,
  },
  contributorInfo: {
    profilePictureBaseUrl: '',
    displayName: '',
  },
  filename: '',
};

const G_MEDIA_ITEM_DETAILS_PHOTO_2: GPhotosMediaItemDetails = {
  id: 'gPhotosMediaItem2',
  description: '',
  productUrl: '',
  baseUrl: 'http://www.google.com/photos/2',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: 300,
    height: 300,
  },
  contributorInfo: {
    profilePictureBaseUrl: '',
    displayName: '',
  },
  filename: '',
};

describe('ImagesListComponent', () => {
  let store: MockStore;
  let mockWindow: Window;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImagesSectionComponent],
      providers: [
        provideNoopAnimations(),
        provideMockStore({
          initialState: {
            [albumsState.FEATURE_KEY]: albumsState.buildInitialState(),
            [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
            [mediaItemsState.FEATURE_KEY]: mediaItemsState.buildInitialState(),
            [gPhotosMediaItemsState.FEATURE_KEY]:
              gPhotosMediaItemsState.buildInitialState(),
          },
        }),
        {
          provide: WINDOW,
          useValue: { open: jasmine.createSpy() },
        },
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    spyOn(store, 'dispatch');

    mockWindow = TestBed.inject(WINDOW);
  });

  it('should render spinner and dispatch correctly given current album is not loaded yet', () => {
    const fixture = TestBed.createComponent(ImagesSectionComponent);
    fixture.componentRef.setInput('albumId', 'album1');
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="images-section-spinner"]',
    );
    expect(spinner).toBeTruthy();
    expect(store.dispatch).toHaveBeenCalledWith(
      albumsActions.loadAlbumDetails({ albumId: 'album1' }),
    );
  });

  it('should render no content given current album has no images', () => {
    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'album1',
          toSuccess({
            ...ALBUM_DETAILS_PHOTOS,
            mediaItemIds: [],
          }),
        ),
      },
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
      [mediaItemsState.FEATURE_KEY]: mediaItemsState.buildInitialState(),
      [gPhotosMediaItemsState.FEATURE_KEY]:
        gPhotosMediaItemsState.buildInitialState(),
    });

    const fixture = TestBed.createComponent(ImagesSectionComponent);
    fixture.componentRef.setInput('albumId', 'album1');
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="images-section-spinner"]',
    );
    expect(spinner).toBeFalsy();
  });

  it('should render spinner and dispatch correctly given media items have not loaded yet', () => {
    const fixture = TestBed.createComponent(ImagesSectionComponent);
    fixture.componentRef.setInput('albumId', 'album1');
    fixture.detectChanges();

    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'album1',
          toSuccess(ALBUM_DETAILS_PHOTOS),
        ),
      },
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
      [mediaItemsState.FEATURE_KEY]: mediaItemsState.buildInitialState(),
      [gPhotosMediaItemsState.FEATURE_KEY]:
        gPhotosMediaItemsState.buildInitialState(),
    });
    store.refreshState();
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="images-section-spinner"]',
    );
    expect(spinner).toBeTruthy();
    expect(store.dispatch).toHaveBeenCalledWith(
      mediaItemsActions.loadMediaItemDetails({ mediaItemId: 'photos1' }),
    );
    expect(store.dispatch).toHaveBeenCalledWith(
      mediaItemsActions.loadMediaItemDetails({ mediaItemId: 'photos2' }),
    );
  });

  it('should render spinner and dispatch correctly given gphotos media items have not loaded yet', () => {
    const fixture = TestBed.createComponent(ImagesSectionComponent);
    fixture.componentRef.setInput('albumId', 'album1');
    fixture.detectChanges();

    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'album1',
          toSuccess(ALBUM_DETAILS_PHOTOS),
        ),
      },
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap()
          .set('photos1', toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_1))
          .set('photos2', toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_2)),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]:
        gPhotosMediaItemsState.buildInitialState(),
    });
    store.refreshState();
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="images-section-spinner"]',
    );
    expect(spinner).toBeTruthy();
    expect(store.dispatch).toHaveBeenCalledWith(
      gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
        gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
      }),
    );
    expect(store.dispatch).toHaveBeenCalledWith(
      gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
        gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem2',
      }),
    );
  });

  it('should render images given gphotos media items have loaded yet', () => {
    const fixture = TestBed.createComponent(ImagesSectionComponent);
    fixture.componentRef.setInput('albumId', 'album1');
    fixture.detectChanges();

    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'album1',
          toSuccess(ALBUM_DETAILS_PHOTOS),
        ),
      },
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap()
          .set('photos1', toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_1))
          .set('photos2', toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_2)),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap()
          .set(
            'gPhotosClient1:gPhotosMediaItem1',
            toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1),
          )
          .set(
            'gPhotosClient1:gPhotosMediaItem2',
            toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_2),
          ),
      },
    });
    store.refreshState();
    fixture.detectChanges();

    const elements = fixture.nativeElement.querySelectorAll(
      '[data-testid="media-item-image"]',
    );
    expect(elements.length).toEqual(2);
    expect(elements[0].src).toEqual('http://www.google.com/photos/1');
    expect(elements[1].src).toEqual('http://www.google.com/photos/2');
  });

  [
    {
      event: new KeyboardEvent('keydown', {
        key: 'Enter',
        code: 'Enter',
      }),
    },
    {
      event: new MouseEvent('click'),
    },
  ].forEach(({ event }) => {
    it(`should dispatch request to open media viewer when user emits ${event} on image`, () => {
      store.setState({
        [albumsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap().set(
            'album1',
            toSuccess(ALBUM_DETAILS_PHOTOS),
          ),
        },
        [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
        [mediaItemsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap()
            .set('photos1', toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_1))
            .set('photos2', toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_2)),
        },
        [gPhotosMediaItemsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap()
            .set(
              'gPhotosClient1:gPhotosMediaItem1',
              toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1),
            )
            .set(
              'gPhotosClient1:gPhotosMediaItem2',
              toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_2),
            ),
        },
      });
      store.refreshState();
      const fixture = TestBed.createComponent(ImagesSectionComponent);
      fixture.componentRef.setInput('albumId', 'album1');
      fixture.detectChanges();

      fixture.nativeElement
        .querySelector('[data-testid="media-item-image"]')
        .dispatchEvent(event);

      expect(store.dispatch).toHaveBeenCalledWith(
        mediaViewerActions.openMediaViewer({
          request: { mediaItemId: 'photos1' },
        }),
      );
    });
  });

  [
    {
      event: new KeyboardEvent('keydown', {
        key: 'Enter',
        code: 'Enter',
        ctrlKey: true,
      }),
    },
    {
      event: new MouseEvent('click', { ctrlKey: true }),
    },
  ].forEach(({ event }) => {
    it(`should dispatch request to open image in new tab when user emits event ${event} on image`, () => {
      store.setState({
        [albumsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap().set(
            'album1',
            toSuccess(ALBUM_DETAILS_PHOTOS),
          ),
        },
        [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
        [mediaItemsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap()
            .set('photos1', toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_1))
            .set('photos2', toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_2)),
        },
        [gPhotosMediaItemsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap()
            .set(
              'gPhotosClient1:gPhotosMediaItem1',
              toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1),
            )
            .set(
              'gPhotosClient1:gPhotosMediaItem2',
              toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_2),
            ),
        },
      });
      store.refreshState();
      const fixture = TestBed.createComponent(ImagesSectionComponent);
      fixture.componentRef.setInput('albumId', 'album1');
      fixture.detectChanges();

      fixture.nativeElement
        .querySelector('[data-testid="media-item-image"]')
        .dispatchEvent(event);

      expect(mockWindow.open).toHaveBeenCalledWith(
        'http://www.google.com/photos/1=w200-h200',
        '_blank',
      );
    });
  });
});
