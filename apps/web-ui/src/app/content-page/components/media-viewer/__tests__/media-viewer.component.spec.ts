import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { NAVIGATOR } from '../../../../app.tokens';
import { authState } from '../../../../auth/store';
import { toSuccess } from '../../../../shared/results/results';
import { GPhotosMediaItem, MediaItem } from '../../../services/webapi.service';
import { gPhotosMediaItemsState } from '../../../store/gphoto-media-items';
import { mediaItemsState } from '../../../store/media-items';
import {
  mediaViewerActions,
  mediaViewerState,
} from '../../../store/media-viewer';
import { MediaViewerComponent } from '../media-viewer.component';

const MEDIA_ITEM_DETAILS: MediaItem = {
  id: 'mediaItem1',
  fileName: 'dog.png',
  hashCode: '',
  location: {
    latitude: 123,
    longitude: 456,
  },
  gPhotosClientId: 'gPhotosClientId1',
  gPhotosMediaItemId: 'gPhotosClientId1:gPhotosMediaItem1',
};

const GPHOTOS_MEDIA_ITEM_DETAILS: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/photos/1',
  mimeType: '',
  mediaMetadata: {
    creationTime: '',
    width: '200',
    height: '300',
  },
};

describe('MediaViewerComponent', () => {
  let mockNavigator: jasmine.SpyObj<Navigator>;
  let component: MediaViewerComponent;
  let fixture: ComponentFixture<MediaViewerComponent>;
  let store: MockStore;

  beforeEach(async () => {
    mockNavigator = jasmine.createSpyObj(Navigator, ['canShare', 'share']);

    await TestBed.configureTestingModule({
      imports: [MediaViewerComponent],
      providers: [
        provideMockStore({
          initialState: {
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
          provide: NAVIGATOR,
          useValue: mockNavigator,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MediaViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    store = TestBed.inject(MockStore);
    spyOn(store, 'dispatch');
  });

  it('should not display dialog and render component', () => {
    const dialog = fixture.nativeElement.querySelector('dialog');
    expect(dialog.open).toBeFalse();

    expect(component).toBeTruthy();
  });

  it('should show dialog and spinner given data is still loading', () => {
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
      },
      [mediaItemsState.FEATURE_KEY]: mediaItemsState.buildInitialState(),
      [gPhotosMediaItemsState.FEATURE_KEY]:
        gPhotosMediaItemsState.buildInitialState(),
    });
    store.refreshState();

    // Assert dialog is open
    const dialog = fixture.nativeElement.querySelector('dialog');
    expect(dialog.open).toBeTrue();

    // Assert spinner is present
    const spinner = fixture.nativeElement.querySelector('.loading-spinner');
    expect(spinner).toBeTruthy();
  });

  it('should render items correctly given data is already loaded', () => {
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
      },
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'mediaItem1',
          toSuccess(MEDIA_ITEM_DETAILS),
        ),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'gPhotosClientId1:gPhotosMediaItem1',
          toSuccess(GPHOTOS_MEDIA_ITEM_DETAILS),
        ),
      },
    });
    store.refreshState();
    fixture.autoDetectChanges();

    // Assert dialog is open
    const dialog = fixture.nativeElement.querySelector('dialog');
    expect(dialog.open).toBeTrue();

    // Assert formatted text is correct
    const formattedText = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-formatted-date-text"]',
    );
    expect(formattedText.textContent!.trim()).toEqual(
      'Sunday, November 20, 2016 at 12:35 PM',
    );

    // Assert the new window button is present
    const newWindowButton = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-new-window-button"]',
    );
    expect(newWindowButton).toBeTruthy();

    // Assert the share button is present
    const shareButton = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-share-button"]',
    );
    expect(shareButton).toBeTruthy();

    // Assert the download button is present
    const downloadButton = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-download-button"]',
    );
    expect(downloadButton).toBeTruthy();

    // Assert the close dialog button is present
    const closeDialogButton = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-close-button"]',
    );
    expect(closeDialogButton).toBeTruthy();

    // Assert the image is present
    const image = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-image"]',
    );
    expect(image.getAttribute('src')).toEqual(
      'http://www.google.com/photos/1=w200-h300',
    );

    // Assert the location text is present
    const locationText = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-location-text"]',
    );
    expect(locationText.textContent!.trim()).toEqual('@ 123, 456');
  });

  it('should not render location when data has no location data', () => {
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
      },
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'mediaItem1',
          toSuccess({
            ...MEDIA_ITEM_DETAILS,
            location: undefined,
          }),
        ),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'gPhotosClientId1:gPhotosMediaItem1',
          toSuccess(GPHOTOS_MEDIA_ITEM_DETAILS),
        ),
      },
    });
    store.refreshState();
    fixture.autoDetectChanges();

    // Assert the location text is not present
    const locationText = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-location-text"]',
    );
    expect(locationText).toBeFalsy();
  });

  it('should call navigator api correctly when user clicks on share button', () => {
    mockNavigator.canShare.and.returnValue(true);
    mockNavigator.share.and.resolveTo(undefined);
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
      },
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'mediaItem1',
          toSuccess(MEDIA_ITEM_DETAILS),
        ),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'gPhotosClientId1:gPhotosMediaItem1',
          toSuccess(GPHOTOS_MEDIA_ITEM_DETAILS),
        ),
      },
    });
    store.refreshState();
    fixture.autoDetectChanges();

    const shareButton = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-share-button"]',
    );
    shareButton.click();

    expect(mockNavigator.share).toHaveBeenCalledWith({
      title: 'dog.png',
      text: 'Photo from Sharded Photos Drive',
      url: 'http://www.google.com/photos/1=w200-h300',
    });
  });

  it('should not call navigator.share() when user clicks on share button but sharing fails', () => {
    mockNavigator.canShare.and.returnValue(false);
    mockNavigator.share.and.resolveTo(undefined);
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
      },
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'mediaItem1',
          toSuccess(MEDIA_ITEM_DETAILS),
        ),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'gPhotosClientId1:gPhotosMediaItem1',
          toSuccess(GPHOTOS_MEDIA_ITEM_DETAILS),
        ),
      },
    });
    store.refreshState();
    fixture.autoDetectChanges();

    const shareButton = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-share-button"]',
    );
    shareButton.click();

    expect(mockNavigator.share).not.toHaveBeenCalled();
  });

  it('should dispatch an event when user clicks on the close button', () => {
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
      },
      [mediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'mediaItem1',
          toSuccess(MEDIA_ITEM_DETAILS),
        ),
      },
      [gPhotosMediaItemsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'gPhotosClientId1:gPhotosMediaItem1',
          toSuccess(GPHOTOS_MEDIA_ITEM_DETAILS),
        ),
      },
    });
    store.refreshState();
    fixture.autoDetectChanges();

    const closeDialogButton = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-close-button"]',
    );
    closeDialogButton.click();
    fixture.autoDetectChanges();

    expect(store.dispatch).toHaveBeenCalledWith(
      mediaViewerActions.closeMediaViewer(),
    );
  });
});
