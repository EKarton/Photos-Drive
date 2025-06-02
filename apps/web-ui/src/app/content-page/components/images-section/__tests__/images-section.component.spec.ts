import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { WINDOW } from '../../../../app.tokens';
import { authState } from '../../../../auth/store';
import {
  GPhotosMediaItem,
  ListMediaItemsInAlbumResponse,
  WebApiService,
} from '../../../services/webapi.service';
import { albumsState } from '../../../store/albums';
import { gPhotosMediaItemsState } from '../../../store/gphoto-media-items';
import { mediaViewerState } from '../../../store/media-viewer';
import { ImagesSectionComponent } from '../images-section.component';

const PAGE_1: ListMediaItemsInAlbumResponse = {
  mediaItems: [
    {
      id: 'photos1',
      fileName: 'dog.png',
      hashCode: '',
      gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
    },
    {
      id: 'photos2',
      fileName: 'cat.png',
      hashCode: '',
      gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem2',
    },
  ],
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

describe('ImagesSectionComponent', () => {
  let store: MockStore;
  let mockWebApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'listMediaItemsInAlbum',
      'fetchGPhotosMediaItemDetails',
    ]);

    await TestBed.configureTestingModule({
      imports: [ImagesSectionComponent],
      providers: [
        provideNoopAnimations(),
        provideMockStore({
          initialState: {
            [albumsState.FEATURE_KEY]: albumsState.buildInitialState(),
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
        {
          provide: WebApiService,
          useValue: mockWebApiService,
        },
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    spyOn(store, 'dispatch');
  });

  it('should render images given album, media items, and gphotos media items have loaded yet', () => {
    mockWebApiService.listMediaItemsInAlbum.and.returnValue(of(PAGE_1));
    mockWebApiService.fetchGPhotosMediaItemDetails.and.returnValues(
      of(G_MEDIA_ITEM_DETAILS_PHOTO_1),
      of(G_MEDIA_ITEM_DETAILS_PHOTO_2),
    );

    const fixture = TestBed.createComponent(ImagesSectionComponent);
    fixture.componentRef.setInput('albumId', 'album1');
    fixture.detectChanges();

    store.setState({
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
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
