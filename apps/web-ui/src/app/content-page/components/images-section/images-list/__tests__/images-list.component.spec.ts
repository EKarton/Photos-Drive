import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';
import { of } from 'rxjs';

import { RESIZE_OBSERVER_FACTORY_TOKEN } from '../../../../../app.tokens';
import { authState } from '../../../../../auth/store';
import { MockResizeObserverFactory } from '../../../../../shared/resize-observer-factory/__mocks__/MockResizeObserverFactory';
import { toSuccess } from '../../../../../shared/results/results';
import {
  GPhotosMediaItem,
  ListMediaItemsInAlbumResponse,
  WebApiService,
} from '../../../../services/webapi.service';
import { gPhotosMediaItemsState } from '../../../../store/gphoto-media-items';
import { mediaViewerState } from '../../../../store/media-viewer';
import { ImagesListComponent } from '../images-list.component';

const PAGE_1: ListMediaItemsInAlbumResponse = {
  mediaItems: [
    {
      id: 'photos1',
      fileName: 'cat.png',
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
  nextPageToken: '123456789',
};

const PAGE_2: ListMediaItemsInAlbumResponse = {
  mediaItems: [
    {
      id: 'photos3',
      fileName: 'lizard.png',
      hashCode: '',
      gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem3',
    },
  ],
};

const GMEDIA_ITEM_DETAILS_PHOTO_1: GPhotosMediaItem = {
  baseUrl: 'https://www.google.com/photos/1',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: '4032',
    height: '3024',
  },
};

const GMEDIA_ITEM_DETAILS_PHOTO_2: GPhotosMediaItem = {
  baseUrl: 'https://www.google.com/photos/2',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: '4032',
    height: '3024',
  },
};

const GMEDIA_ITEM_DETAILS_PHOTO_3: GPhotosMediaItem = {
  baseUrl: 'https://www.google.com/photos/3',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: '4032',
    height: '3024',
  },
};

describe('ImagesListComponent', () => {
  let mockWebApiService: jasmine.SpyObj<WebApiService>;
  let mockResizeObserverFactory: MockResizeObserverFactory;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'listMediaItemsInAlbum',
      'fetchGPhotosMediaItemDetails',
    ]);

    await TestBed.configureTestingModule({
      imports: [ImagesListComponent],
      providers: [
        provideNoopAnimations(),
        provideMockStore({
          initialState: {
            [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
            [gPhotosMediaItemsState.FEATURE_KEY]: {
              idToDetails: ImmutableMap()
                .set(
                  'gPhotosClient1:gPhotosMediaItem1',
                  toSuccess(GMEDIA_ITEM_DETAILS_PHOTO_1),
                )
                .set(
                  'gPhotosClient1:gPhotosMediaItem2',
                  toSuccess(GMEDIA_ITEM_DETAILS_PHOTO_2),
                )
                .set(
                  'gPhotosClient1:gPhotosMediaItem3',
                  toSuccess(GMEDIA_ITEM_DETAILS_PHOTO_3),
                ),
            },
          },
          selectors: [
            { selector: authState.selectAuthToken, value: 'mockAccessToken' },
          ],
        }),
        { provide: WebApiService, useValue: mockWebApiService },
        {
          provide: RESIZE_OBSERVER_FACTORY_TOKEN,
          useValue: new MockResizeObserverFactory(),
        },
      ],
    }).compileComponents();

    mockResizeObserverFactory = TestBed.inject(
      RESIZE_OBSERVER_FACTORY_TOKEN,
    ) as MockResizeObserverFactory;
  });

  it('should render images', () => {
    mockWebApiService.listMediaItemsInAlbum.and.returnValues(
      of(PAGE_1),
      of(PAGE_2),
    );

    const fixture = TestBed.createComponent(ImagesListComponent);
    fixture.componentRef.setInput('albumId', ['album1']);
    fixture.detectChanges();

    const elements = fixture.nativeElement.querySelectorAll('img');
    expect(elements.length).toEqual(2);
    expect(elements[0].src).toEqual('https://www.google.com/photos/1');
    expect(elements[1].src).toEqual('https://www.google.com/photos/2');
  });

  [
    {
      hostElementWidth: 200,
      expectedImageWidths: [95, 95],
      expectedImageHeights: [95, 95],
    },
    {
      hostElementWidth: 500,
      expectedImageWidths: [160, 160],
      expectedImageHeights: [160, 160],
    },
    {
      hostElementWidth: 1200,
      expectedImageWidths: [292, 292],
      expectedImageHeights: [292, 292],
    },
    {
      hostElementWidth: 1600,
      expectedImageWidths: [312, 312],
      expectedImageHeights: [312, 312],
    },
  ].forEach(
    ({ hostElementWidth, expectedImageWidths, expectedImageHeights }) => {
      it(`should resize images correctly when the component width changes to ${hostElementWidth}`, async () => {
        mockWebApiService.listMediaItemsInAlbum.and.returnValues(
          of(PAGE_1),
          of(PAGE_2),
        );

        // Render the component
        const fixture = TestBed.createComponent(ImagesListComponent);
        fixture.componentRef.setInput('albumId', ['album1']);
        fixture.detectChanges();

        // Simulate a resize event
        const entry: ResizeObserverEntry = {
          borderBoxSize: [],
          contentBoxSize: [],
          contentRect: {
            bottom: 0,
            height: 0,
            left: 0,
            right: 0,
            top: 0,
            width: hostElementWidth,
            x: 0,
            y: 0,
            toJSON: () => Object,
          },
          devicePixelContentBoxSize: [],
          target: fixture.nativeElement,
        };

        // Trigger the observer's callback
        mockResizeObserverFactory.getInstances()[0].trigger([entry]);
        fixture.detectChanges();
        await fixture.whenStable();

        // Assert the images resized correctly
        const elements: HTMLImageElement[] = Array.from(
          fixture.nativeElement.querySelectorAll('img'),
        );
        const widths = Array.from(elements).map((e) => e.width);
        const heights = Array.from(elements).map((e) => e.height);
        expect(widths).toEqual(expectedImageWidths);
        expect(heights).toEqual(expectedImageHeights);
      });
    },
  );

  it('should fetch more images given user has scrolled', () => {
    mockWebApiService.listMediaItemsInAlbum.and.returnValues(
      of(PAGE_1),
      of(PAGE_2),
    );

    const fixture = TestBed.createComponent(ImagesListComponent);
    fixture.componentRef.setInput('albumId', ['album1']);
    fixture.detectChanges();

    fixture.componentInstance.loadMoreMediaItems();
    fixture.detectChanges();

    expect(fixture.componentInstance.images().length).toEqual(3);
  });
});
