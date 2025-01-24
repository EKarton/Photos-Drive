import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { WINDOW } from '../../../../app.tokens';
import { authState } from '../../../../auth/store';
import { toSuccess } from '../../../../shared/results/results';
import { GPhotosMediaItemDetails } from '../../../services/gphotos-api.service';
import { Album, MediaItem } from '../../../services/webapi.service';
import { albumsActions, albumsState } from '../../../store/albums';
import { gPhotosMediaItemsState } from '../../../store/gphoto-media-items';
import { mediaItemsState } from '../../../store/media-items';
import { mediaViewerState } from '../../../store/media-viewer';
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

describe('ImagesSectionComponent', () => {
  let store: MockStore;

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
          selectors: [
            { selector: authState.selectAuthToken, value: 'mockAccessToken' },
          ],
        }),
        {
          provide: WINDOW,
          useValue: { open: jasmine.createSpy() },
        },
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    spyOn(store, 'dispatch');
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

  it('should render images given album, media items, and gphotos media items have loaded yet', () => {
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
});
