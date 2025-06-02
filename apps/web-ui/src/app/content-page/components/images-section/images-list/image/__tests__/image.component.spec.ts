import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { WINDOW } from '../../../../../../app.tokens';
import { toSuccess } from '../../../../../../shared/results/results';
import { GPhotosMediaItem } from '../../../../../services/webapi.service';
import {
  gPhotosMediaItemsActions,
  gPhotosMediaItemsState,
} from '../../../../../store/gphoto-media-items';
import {
  mediaViewerActions,
  mediaViewerState,
} from '../../../../../store/media-viewer';
import { ImageComponent } from '../image.component';

const G_MEDIA_ITEM_DETAILS_PHOTO_1: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/photos/1',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: '4032',
    height: '3024',
  },
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
    fixture.componentRef.setInput('gPhotosMediaItemId', 'gPhotos1');
    fixture.componentRef.setInput('fileName', 'dog.png');
    fixture.componentRef.setInput('width', 250);
    fixture.componentRef.setInput('height', 300);
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="image-loading"]',
    );
    expect(spinner).toBeTruthy();
  });

  it('should render image when gmedia item has loaded already', () => {
    const fixture = TestBed.createComponent(ImageComponent);
    fixture.componentRef.setInput('mediaItemId', 'photos1');
    fixture.componentRef.setInput('gPhotosMediaItemId', 'gPhotos1');
    fixture.componentRef.setInput('fileName', 'dog.png');
    fixture.componentRef.setInput('width', 250);
    fixture.componentRef.setInput('height', 300);
    fixture.detectChanges();

    store.setState({
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'gPhotos1',
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

  it('should dispatch event to load gphotos media item when media item is only loaded and it is in viewport', () => {
    store.setState({
      [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
      [gPhotosMediaItemsState.FEATURE_KEY]:
        gPhotosMediaItemsState.buildInitialState(),
    });
    const fixture = TestBed.createComponent(ImageComponent);
    fixture.componentRef.setInput('mediaItemId', 'photos1');
    fixture.componentRef.setInput('gPhotosMediaItemId', 'gPhotos1');
    fixture.componentRef.setInput('fileName', 'dog.png');
    fixture.componentRef.setInput('width', 250);
    fixture.componentRef.setInput('height', 300);
    fixture.detectChanges();

    fixture.componentInstance.setIsInViewport(true);
    fixture.detectChanges();

    expect(store.dispatch).toHaveBeenCalledWith(
      gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
        gMediaItemId: 'gPhotos1',
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
      fixture.componentRef.setInput('gPhotosMediaItemId', 'gPhotos1');
      fixture.componentRef.setInput('fileName', 'dog.png');
      fixture.componentRef.setInput('width', 250);
      fixture.componentRef.setInput('height', 300);
      fixture.detectChanges();

      store.setState({
        [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
        [gPhotosMediaItemsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap().set(
            'gPhotos1',
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
      fixture.componentRef.setInput('gPhotosMediaItemId', 'gPhotos1');
      fixture.componentRef.setInput('fileName', 'dog.png');
      fixture.componentRef.setInput('width', 250);
      fixture.componentRef.setInput('height', 300);
      fixture.detectChanges();

      store.setState({
        [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
        [gPhotosMediaItemsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap().set(
            'gPhotos1',
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
