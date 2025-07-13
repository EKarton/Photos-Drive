import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { MAPBOX_FACTORY_TOKEN, WINDOW } from '../../../../app.tokens';
import { authState } from '../../../../auth/store';
import { MockMapboxFactory } from '../../../../shared/mapbox-factory/__mocks__/MockMapboxFactory';
import { toSuccess } from '../../../../shared/results/results';
import { themeState } from '../../../../themes/store';
import { ListMediaItemsResponse } from '../../../services/types/list-media-items';
import { WebApiService } from '../../../services/webapi.service';
import { albumsState } from '../../../store/albums';
import { mediaViewerState } from '../../../store/media-viewer';
import { ImageMapMarkerComponent } from '../images-map/images-map-viewer/image-map-marker/image-map-marker.component';
import { ImagesSectionComponent } from '../images-section.component';

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

describe('ImagesSectionComponent', () => {
  let store: MockStore;
  let mockWebApiService: jasmine.SpyObj<WebApiService>;
  let mockMapboxFactory: MockMapboxFactory<ImageMapMarkerComponent>;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'listMediaItems',
    ]);
    mockMapboxFactory = new MockMapboxFactory();

    await TestBed.configureTestingModule({
      imports: [ImagesSectionComponent],
      providers: [
        provideNoopAnimations(),
        provideMockStore({
          initialState: {
            [albumsState.FEATURE_KEY]: albumsState.buildInitialState(),
          },
          selectors: [
            { selector: authState.selectAuthToken, value: 'mockAccessToken' },
            { selector: themeState.selectIsDarkMode, value: false },
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
        {
          provide: MAPBOX_FACTORY_TOKEN,
          useValue: mockMapboxFactory,
        },
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    spyOn(store, 'dispatch');
  });

  it('should render list of images given album, media items, and gphotos media items have loaded yet', () => {
    mockWebApiService.listMediaItems.and.returnValue(of(toSuccess(PAGE_1)));

    const fixture = TestBed.createComponent(ImagesSectionComponent);
    fixture.componentRef.setInput('albumId', 'album1');
    fixture.detectChanges();

    store.setState({
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
    });
    store.refreshState();
    fixture.detectChanges();

    const elements = fixture.nativeElement.querySelectorAll('app-image');
    expect(elements.length).toEqual(2);
  });

  it('should render map of images when user changes view to map view', () => {
    mockWebApiService.listMediaItems.and.returnValue(of(toSuccess(PAGE_1)));
    const fixture = TestBed.createComponent(ImagesSectionComponent);
    fixture.componentRef.setInput('albumId', 'album1');
    fixture.detectChanges();

    fixture.nativeElement
      .querySelector('app-content-images-view-dropdown')
      .click();
    fixture.detectChanges();
    fixture.nativeElement
      .querySelector('[data-testid="map-view-radio-button"]')
      .click();
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelector('app-content-images-map'),
    ).toBeTruthy();
  });
});
