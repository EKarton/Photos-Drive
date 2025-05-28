import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { RESIZE_OBSERVER_FACTORY_TOKEN } from '../../../../../app.tokens';
import { MockResizeObserverFactory } from '../../../../../shared/resize-observer-factory/__mocks__/MockResizeObserverFactory';
import { toSuccess } from '../../../../../shared/results/results';
import {
  GPhotosMediaItem,
  MediaItem,
} from '../../../../services/webapi.service';
import { gPhotosMediaItemsState } from '../../../../store/gphoto-media-items';
import { mediaItemsState } from '../../../../store/media-items';
import { mediaViewerState } from '../../../../store/media-viewer';
import { ImagesListComponent } from '../images-list.component';

const MEDIA_ITEM_DETAILS_PHOTOS_1: MediaItem = {
  id: 'photos1',
  fileName: 'cat.png',
  hashCode: '',
  gPhotosClientId: 'gPhotosClient1',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
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

describe('ImagesListComponent', () => {
  let mockResizeObserverFactory: MockResizeObserverFactory;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImagesListComponent],
      providers: [
        provideNoopAnimations(),
        provideMockStore({
          initialState: {
            [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
            [mediaItemsState.FEATURE_KEY]: {
              idToDetails: ImmutableMap().set(
                'photos1',
                toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_1),
              ),
            },
            [gPhotosMediaItemsState.FEATURE_KEY]: {
              idToDetails: ImmutableMap().set(
                'gPhotosClient1:gPhotosMediaItem1',
                toSuccess(GMEDIA_ITEM_DETAILS_PHOTO_1),
              ),
            },
          },
        }),
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
    const fixture = TestBed.createComponent(ImagesListComponent);
    fixture.componentRef.setInput('mediaItemIds', ['photos1']);
    fixture.detectChanges();

    const elements = fixture.nativeElement.querySelectorAll('img');
    expect(elements.length).toEqual(1);
    expect(elements[0].src).toEqual('https://www.google.com/photos/1');

    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  [
    {
      hostElementWidth: 200,
      expectedImageWidths: [95],
      expectedImageHeights: [71],
    },
    {
      hostElementWidth: 500,
      expectedImageWidths: [160],
      expectedImageHeights: [120],
    },
    {
      hostElementWidth: 1200,
      expectedImageWidths: [292],
      expectedImageHeights: [219],
    },
    {
      hostElementWidth: 1600,
      expectedImageWidths: [312],
      expectedImageHeights: [234],
    },
  ].forEach(
    ({ hostElementWidth, expectedImageWidths, expectedImageHeights }) => {
      it(`should resize images correctly when the component width changes to ${hostElementWidth}`, async () => {
        // Render the component
        const fixture = TestBed.createComponent(ImagesListComponent);
        fixture.componentRef.setInput('mediaItemIds', ['photos1']);
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
    const mediaItemIds = Array.from(
      { length: 1000 },
      (_, i) => `photos${i + 1}`,
    );
    const fixture = TestBed.createComponent(ImagesListComponent);
    fixture.componentRef.setInput('mediaItemIds', mediaItemIds);
    fixture.detectChanges();

    fixture.componentInstance.getMoreMediaItemIds();
    fixture.detectChanges();

    expect(fixture.componentInstance.paginatedMediaItemIds().length).toEqual(
      100,
    );
  });
});
