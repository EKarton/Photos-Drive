import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { WINDOW } from '../../../../../../app.tokens';
import { toFailure, toSuccess } from '../../../../../../shared/results/results';
import { GPhotosMediaItemDetails } from '../../../../../services/gphotos-api.service';
import { MediaItem } from '../../../../../services/webapi.service';
import {
  gPhotosMediaItemsActions,
  gPhotosMediaItemsState,
} from '../../../../../store/gphoto-media-items';
import {
  mediaItemsActions,
  mediaItemsState,
} from '../../../../../store/media-items';
import {
  mediaViewerActions,
  mediaViewerState,
} from '../../../../../store/media-viewer';
import { ImageComponent } from '../image.component';

const MEDIA_ITEM_DETAILS_PHOTOS_1: MediaItem = {
  id: 'photos1',
  fileName: 'cat.png',
  hashCode: '',
  gPhotosClientId: 'gPhotosClient1',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
};

const G_MEDIA_ITEM_DETAILS_PHOTO_1: GPhotosMediaItemDetails = {
  id: 'gPhotosMediaItem1',
  description: '',
  productUrl: '',
  baseUrl: 'http://www.google.com/photos/1',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: 4032,
    height: 3024,
  },
  contributorInfo: {
    profilePictureBaseUrl: '',
    displayName: '',
  },
  filename: '',
};

describe('ImageComponent', () => {
  let store: MockStore;
  let mockWindow: Window;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImageComponent],
      providers: [
        provideNoopAnimations(),
        provideMockStore({
          initialState: {
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

  it('should render skeleton when media item is not loaded yet', () => {
    const fixture = TestBed.createComponent(ImageComponent);
    fixture.componentRef.setInput('mediaItemId', 'photos1');
    fixture.componentRef.setInput('width', 250);
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="image-loading"]',
    );
    expect(spinner).toBeTruthy();
  });

  it('should show error when media item has failed to load', () => {
    const fixture = TestBed.createComponent(ImageComponent);
    fixture.componentRef.setInput('mediaItemId', 'photos1');
    fixture.componentRef.setInput('width', 250);
    fixture.detectChanges();

    store.setState({
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
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

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="image-error"]',
    );
    expect(spinner).toBeTruthy();
  });

  it('should render image when media item has loaded already', () => {
    const fixture = TestBed.createComponent(ImageComponent);
    fixture.componentRef.setInput('mediaItemId', 'photos1');
    fixture.componentRef.setInput('width', 250);
    fixture.detectChanges();

    store.setState({
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
          toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1),
        ),
      },
    });
    store.refreshState();
    fixture.detectChanges();

    const image = fixture.nativeElement.querySelector(
      '[data-testid="media-item-image"]',
    );
    expect(image.src).toEqual('http://www.google.com/photos/1');
    expect(image.width).toEqual(250);
    expect(image.width).toEqual(250);
  });

  it('should dispatch event to load media item when it is not loaded yet and it is in viewport', () => {
    const fixture = TestBed.createComponent(ImageComponent);
    fixture.componentRef.setInput('mediaItemId', 'photos1');
    fixture.componentRef.setInput('width', 250);
    fixture.detectChanges();

    fixture.componentInstance.setIsInViewport(true);
    fixture.detectChanges();

    expect(store.dispatch).toHaveBeenCalledWith(
      mediaItemsActions.loadMediaItemDetails({ mediaItemId: 'photos1' }),
    );
  });

  it('should dispatch event to load gphotos media item when media item is only loaded and it is in viewport', () => {
    store.setState({
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'photos1',
          toSuccess(MEDIA_ITEM_DETAILS_PHOTOS_1),
        ),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]:
        gPhotosMediaItemsState.buildInitialState(),
    });
    const fixture = TestBed.createComponent(ImageComponent);
    fixture.componentRef.setInput('mediaItemId', 'photos1');
    fixture.componentRef.setInput('width', 250);
    fixture.detectChanges();

    fixture.componentInstance.setIsInViewport(true);
    fixture.detectChanges();

    expect(store.dispatch).toHaveBeenCalledWith(
      gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
        gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
      }),
    );
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
      const fixture = TestBed.createComponent(ImageComponent);
      fixture.componentRef.setInput('mediaItemId', 'photos1');
      fixture.componentRef.setInput('width', 250);
      fixture.detectChanges();

      store.setState({
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
            toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1),
          ),
        },
      });
      store.refreshState();
      fixture.detectChanges();

      fixture.nativeElement
        .querySelector('[data-testid="media-item-image"]')
        .dispatchEvent(event);

      expect(mockWindow.open).toHaveBeenCalledWith(
        'http://www.google.com/photos/1=w4032-h3024',
        '_blank',
      );
    });
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
      const fixture = TestBed.createComponent(ImageComponent);
      fixture.componentRef.setInput('mediaItemId', 'photos1');
      fixture.componentRef.setInput('width', 250);
      fixture.detectChanges();

      store.setState({
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
            toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1),
          ),
        },
      });
      store.refreshState();
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
});
