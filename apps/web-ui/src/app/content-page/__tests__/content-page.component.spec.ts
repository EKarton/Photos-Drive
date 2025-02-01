import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ActivatedRoute } from '@angular/router';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';
import { of } from 'rxjs';

import { authState } from '../../auth/store';
import { toSuccess } from '../../shared/results/results';
import { themeState } from '../../themes/store';
import { ContentPageComponent } from '../content-page.component';
import { Album, GPhotosMediaItem, MediaItem } from '../services/webapi.service';
import { albumsState } from '../store/albums';
import { gPhotosMediaItemsState } from '../store/gphoto-media-items';
import { gPhotosClientsState } from '../store/gphotos-clients';
import { mediaItemsState } from '../store/media-items';
import { mediaViewerState } from '../store/media-viewer';

const ALBUM_DETAILS_ROOT: Album = {
  id: 'album1',
  albumName: '',
  childAlbumIds: ['album2'],
  mediaItemIds: [],
};

const ALBUM_DETAILS_ARCHIVES: Album = {
  id: 'album2',
  albumName: 'Archives',
  parentAlbumId: 'album1',
  childAlbumIds: ['album3'],
  mediaItemIds: [],
};

const ALBUM_DETAILS_PHOTOS: Album = {
  id: 'album3',
  albumName: 'Photos',
  parentAlbumId: 'album2',
  childAlbumIds: ['album4', 'album5'],
  mediaItemIds: ['photos1', 'photos2'],
};

const ALBUM_DETAILS_2010: Album = {
  id: 'album4',
  albumName: '2010',
  parentAlbumId: 'album3',
  childAlbumIds: [],
  mediaItemIds: [],
};

const ALBUM_DETAILS_2011: Album = {
  id: 'album5',
  albumName: '2011',
  parentAlbumId: 'album3',
  childAlbumIds: [],
  mediaItemIds: [],
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

const G_MEDIA_ITEM_DETAILS_PHOTO_1: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/photos/1',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: '200',
    height: '200',
  },
};

const G_MEDIA_ITEM_DETAILS_PHOTO_2: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/photos/2',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: '300',
    height: '300',
  },
};

describe('ContentPageComponent', () => {
  let component: ContentPageComponent;
  let fixture: ComponentFixture<ContentPageComponent>;
  let store: MockStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ContentPageComponent],
      providers: [
        provideMockStore({
          initialState: {
            [albumsState.FEATURE_KEY]: albumsState.buildInitialState(),
            [mediaItemsState.FEATURE_KEY]: mediaItemsState.buildInitialState(),
            [gPhotosMediaItemsState.FEATURE_KEY]:
              gPhotosMediaItemsState.buildInitialState(),
            [mediaViewerState.FEATURE_KEY]: mediaItemsState.buildInitialState(),
            [gPhotosClientsState.FEATURE_KEY]: gPhotosClientsState.initialState,
            [themeState.FEATURE_KEY]: themeState.initialState,
            [authState.FEATURE_KEY]: authState.buildInitialState(),
          },
        }),
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(ImmutableMap().set('albumId', 'album3')),
          },
        },
        provideNoopAnimations(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ContentPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    store = TestBed.inject(MockStore);
  });

  it('should show loading state given nothing is loaded yet', () => {
    expect(component).toBeTruthy();
    expect(fixture.nativeElement.querySelector('.skeleton')).toBeTruthy();
  });

  it('should show albums and photos given data has been loaded', () => {
    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap()
          .set('album1', toSuccess(ALBUM_DETAILS_ROOT))
          .set('album2', toSuccess(ALBUM_DETAILS_ARCHIVES))
          .set('album3', toSuccess(ALBUM_DETAILS_PHOTOS))
          .set('album4', toSuccess(ALBUM_DETAILS_2010))
          .set('album5', toSuccess(ALBUM_DETAILS_2011)),
      },
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
      [mediaViewerState.FEATURE_KEY]: mediaItemsState.buildInitialState(),
      [gPhotosClientsState.FEATURE_KEY]: gPhotosClientsState.initialState,
      [themeState.FEATURE_KEY]: themeState.initialState,
      [authState.FEATURE_KEY]: authState.buildInitialState(),
    });
    store.refreshState();
    fixture.detectChanges();

    // Assert that the breadcrumbs render correctly
    const breadcrumbLinks = fixture.nativeElement.querySelectorAll(
      '[data-testid="breadcrumb-link"]',
    );
    expect(breadcrumbLinks.length).toEqual(3);
    expect(breadcrumbLinks[0].textContent).toEqual('Home');
    expect(breadcrumbLinks[1].textContent).toEqual('Archives');
    expect(breadcrumbLinks[2].textContent).toEqual('Photos');

    // Assert that the sub-albums are rendered
    const subAlbums = fixture.nativeElement.querySelectorAll(
      '[data-testid="album-card-name"]',
    );
    expect(subAlbums.length).toBe(2);
    expect(subAlbums[0].textContent!.trim()).toBe('2010');
    expect(subAlbums[1].textContent!.trim()).toBe('2011');

    // Assert that the images rendered correctly
    const mediaItemImages = fixture.nativeElement.querySelectorAll(
      '[data-testid="media-item-image"]',
    );
    expect(mediaItemImages.length).toEqual(2);
    expect(mediaItemImages[0].getAttribute('src')).toEqual(
      'http://www.google.com/photos/1',
    );
    expect(mediaItemImages[1].getAttribute('src')).toEqual(
      'http://www.google.com/photos/2',
    );
  });

  it('should show "There are no albums and no photos in this album." when there are no child albums and no media items in the current album', () => {
    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap()
          .set('album1', toSuccess(ALBUM_DETAILS_ROOT))
          .set('album2', toSuccess(ALBUM_DETAILS_ARCHIVES))
          .set(
            'album3',
            toSuccess({
              id: 'album3',
              albumName: '2010',
              parentAlbumId: 'album2',
              childAlbumIds: [],
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
      [mediaViewerState.FEATURE_KEY]: mediaItemsState.buildInitialState(),
      [gPhotosClientsState.FEATURE_KEY]: gPhotosClientsState.initialState,
      [themeState.FEATURE_KEY]: themeState.initialState,
      [authState.FEATURE_KEY]: authState.buildInitialState(),
    });
    store.refreshState();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain(
      'There are no albums and no photos in this album.',
    );
  });
});
