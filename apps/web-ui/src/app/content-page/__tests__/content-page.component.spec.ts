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
import { Album } from '../services/types/album';
import { ListAlbumsResponse } from '../services/types/list-albums';
import { ListMediaItemsResponse } from '../services/types/list-media-items';
import { WebApiService } from '../services/webapi.service';
import { albumsState } from '../store/albums';
import { mediaViewerState } from '../store/media-viewer';

const ALBUM_DETAILS_ROOT: Album = {
  id: 'album1',
  albumName: '',
  childAlbumIds: ['album2'],
  numChildAlbums: 1,
  numMediaItems: 0,
};

const ALBUM_DETAILS_ARCHIVES: Album = {
  id: 'album2',
  albumName: 'Archives',
  parentAlbumId: 'album1',
  childAlbumIds: ['album3'],
  numChildAlbums: 1,
  numMediaItems: 0,
};

const ALBUM_DETAILS_PHOTOS: Album = {
  id: 'album3',
  albumName: 'Photos',
  parentAlbumId: 'album2',
  childAlbumIds: ['album4', 'album5'],
  numChildAlbums: 2,
  numMediaItems: 2,
};

const ALBUM_DETAILS_2010: Album = {
  id: 'album4',
  albumName: '2010',
  parentAlbumId: 'album3',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 0,
};

const ALBUM_DETAILS_2011: Album = {
  id: 'album5',
  albumName: '2011',
  parentAlbumId: 'album3',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 0,
};

const PAGE_1: ListMediaItemsResponse = {
  mediaItems: [
    {
      id: 'photos1',
      fileName: 'dog.png',
      hashCode: '',
      gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
      width: 200,
      height: 300,
      dateTaken: new Date('2024-05-27T13:17:46.000Z'),
    },
    {
      id: 'photos2',
      fileName: 'cat.png',
      hashCode: '',
      gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem2',
      width: 200,
      height: 300,
      dateTaken: new Date('2024-05-27T13:17:46.000Z'),
    },
  ],
};

describe('ContentPageComponent', () => {
  let component: ContentPageComponent;
  let fixture: ComponentFixture<ContentPageComponent>;
  let store: MockStore;
  let mockWebApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'listMediaItems',
      'listAlbums',
    ]);

    await TestBed.configureTestingModule({
      imports: [ContentPageComponent],
      providers: [
        provideMockStore({
          initialState: {
            [albumsState.FEATURE_KEY]: albumsState.buildInitialState(),
            [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
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
        {
          provide: WebApiService,
          useValue: mockWebApiService,
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

  it('should show albums and photos given data has been loaded', async () => {
    mockWebApiService.listMediaItems.and.returnValue(of(toSuccess(PAGE_1)));
    mockWebApiService.listAlbums.and.returnValue(
      of(
        toSuccess<ListAlbumsResponse>({
          albums: [ALBUM_DETAILS_2010, ALBUM_DETAILS_2011],
        }),
      ),
    );
    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap()
          .set('album1', toSuccess(ALBUM_DETAILS_ROOT))
          .set('album2', toSuccess(ALBUM_DETAILS_ARCHIVES))
          .set('album3', toSuccess(ALBUM_DETAILS_PHOTOS))
          .set('album4', toSuccess(ALBUM_DETAILS_2010))
          .set('album5', toSuccess(ALBUM_DETAILS_2011)),
      },
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
      [themeState.FEATURE_KEY]: themeState.initialState,
      [authState.FEATURE_KEY]: authState.buildInitialState(),
    });
    store.refreshState();
    fixture.detectChanges();
    await fixture.whenStable();

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
    const mediaItemImages = fixture.nativeElement.querySelectorAll('app-image');
    expect(mediaItemImages.length).toEqual(2);
  });

  it('should show "There are no albums and no photos in this album." when there are no child albums and no media items in the current album', async () => {
    mockWebApiService.listMediaItems.and.returnValue(
      of(
        toSuccess({
          mediaItems: [],
        }),
      ),
    );
    mockWebApiService.listAlbums.and.returnValue(
      of(
        toSuccess<ListAlbumsResponse>({
          albums: [],
        }),
      ),
    );
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
              numChildAlbums: 0,
              numMediaItems: 0,
            }),
          ),
      },
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
      [themeState.FEATURE_KEY]: themeState.initialState,
      [authState.FEATURE_KEY]: authState.buildInitialState(),
    });
    store.refreshState();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain(
      'There are no albums and no photos in this album.',
    );
  });
});
