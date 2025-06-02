import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { NAVIGATOR } from '../../../../app.tokens';
import { authState } from '../../../../auth/store';
import { toPending, toSuccess } from '../../../../shared/results/results';
import {
  GPhotosMediaItem,
  GPhotosMediaItemDetailsApiResponse,
  MediaItem,
  MediaItemDetailsApiResponse,
  WebApiService,
} from '../../../services/webapi.service';
import {
  mediaViewerActions,
  mediaViewerState,
} from '../../../store/media-viewer';
import { MediaViewerComponent } from '../media-viewer.component';

const MEDIA_ITEM_IMAGE: MediaItem = {
  id: 'mediaItem1',
  fileName: 'dog.png',
  hashCode: '1234',
  location: {
    latitude: 123,
    longitude: 456,
  },
  gPhotosMediaItemId: 'gPhotosClientId1:gPhotosMediaItem1',
};

const GPHOTOS_MEDIA_ITEM_IMAGE: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/photos/1',
  mimeType: 'image/png',
  mediaMetadata: {
    creationTime: '',
    width: '200',
    height: '300',
  },
};

const MEDIA_ITEM_VIDEO: MediaItem = {
  id: 'mediaItem2',
  fileName: 'dog.mp4',
  hashCode: '1234',
  location: {
    latitude: 123,
    longitude: 456,
  },
  gPhotosMediaItemId: 'gPhotosClientId1:gPhotosMediaItem2',
};

const GPHOTOS_MEDIA_ITEM_VIDEO: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/videos/1',
  mimeType: 'video/mp4',
  mediaMetadata: {
    creationTime: '',
    width: '200',
    height: '300',
  },
};

const MEDIA_ITEM_AUDIO: MediaItem = {
  id: 'mediaItem3',
  fileName: 'dog.mp3',
  hashCode: '1234',
  gPhotosMediaItemId: 'gPhotosClientId1:gPhotosMediaItem3',
};

const GPHOTOS_MEDIA_ITEM_AUDIO: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/audio/1',
  mimeType: 'audio/mp3',
  mediaMetadata: {
    creationTime: '',
  },
};

describe('MediaViewerComponent', () => {
  let mockNavigator: jasmine.SpyObj<Navigator>;
  let component: MediaViewerComponent;
  let fixture: ComponentFixture<MediaViewerComponent>;
  let store: MockStore;
  let mockWebApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(async () => {
    mockNavigator = jasmine.createSpyObj(Navigator, ['canShare', 'share']);
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'getMediaItem',
      'getGPhotosMediaItem',
    ]);

    await TestBed.configureTestingModule({
      imports: [MediaViewerComponent],
      providers: [
        provideMockStore({
          initialState: {
            [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
          },
          selectors: [
            { selector: authState.selectAuthToken, value: 'mockAccessToken' },
          ],
        }),
        { provide: NAVIGATOR, useValue: mockNavigator },
        { provide: WebApiService, useValue: mockWebApiService },
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
    mockWebApiService.getMediaItem.and.returnValue(
      of(toPending<MediaItemDetailsApiResponse>()),
    );
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toPending<GPhotosMediaItemDetailsApiResponse>()),
    );
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
      },
    });
    store.refreshState();

    // Assert dialog is open
    const dialog = fixture.nativeElement.querySelector('dialog');
    expect(dialog.open).toBeTrue();

    // Assert spinner is present
    const spinner = fixture.nativeElement.querySelector('.loading-spinner');
    expect(spinner).toBeTruthy();
  });

  it('should render error message given unhandled mime type', () => {
    mockWebApiService.getMediaItem.and.returnValue(
      of(toSuccess(MEDIA_ITEM_AUDIO)),
    );
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(GPHOTOS_MEDIA_ITEM_AUDIO)),
    );

    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem3',
        },
        isOpen: true,
      },
    });
    store.refreshState();
    fixture.autoDetectChanges();

    // Assert dialog is open
    const dialog = fixture.nativeElement.querySelector('dialog');
    expect(dialog.open).toBeTrue();

    // Assert error message on content viewer is present
    const errorMessage = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-unknown"]',
    );
    expect(errorMessage.textContent!.trim()).toEqual(
      'Unhandled media type: audio/mp3',
    );
  });

  it('should render items correctly given loaded image data', () => {
    mockWebApiService.getMediaItem.and.returnValue(
      of(toSuccess(MEDIA_ITEM_IMAGE)),
    );
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(GPHOTOS_MEDIA_ITEM_IMAGE)),
    );

    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
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
    expect(newWindowButton.getAttribute('href')).toEqual(
      'http://www.google.com/photos/1=w200-h300',
    );

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
    expect(downloadButton.getAttribute('href')).toEqual(
      'http://www.google.com/photos/1=d',
    );
    expect(downloadButton.getAttribute('download')).toEqual('dog.png');

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

  it('should render items correctly given loaded video data', () => {
    mockWebApiService.getMediaItem.and.returnValue(
      of(toSuccess(MEDIA_ITEM_VIDEO)),
    );
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(GPHOTOS_MEDIA_ITEM_VIDEO)),
    );
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem2',
        },
        isOpen: true,
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
    expect(newWindowButton.getAttribute('href')).toEqual(
      'http://www.google.com/videos/1=dv',
    );

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
    expect(downloadButton.getAttribute('href')).toEqual(
      'http://www.google.com/videos/1=dv',
    );
    expect(downloadButton.getAttribute('download')).toEqual('dog.mp4');

    // Assert the close dialog button is present
    const closeDialogButton = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-close-button"]',
    );
    expect(closeDialogButton).toBeTruthy();

    // Assert the video is present
    const video = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-video"]',
    );
    expect(video).toBeTruthy();

    // Assert the location text is present
    const locationText = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-location-text"]',
    );
    expect(locationText.textContent!.trim()).toEqual('@ 123, 456');
  });

  it('should not render location when data has no location data', () => {
    mockWebApiService.getMediaItem.and.returnValue(
      of(
        toSuccess({
          ...MEDIA_ITEM_IMAGE,
          location: undefined,
        }),
      ),
    );
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(GPHOTOS_MEDIA_ITEM_IMAGE)),
    );
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
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

  it('should call navigator api correctly when user clicks on share button on an image', () => {
    mockNavigator.canShare.and.returnValue(true);
    mockNavigator.share.and.resolveTo(undefined);
    mockWebApiService.getMediaItem.and.returnValue(
      of(toSuccess(MEDIA_ITEM_IMAGE)),
    );
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(GPHOTOS_MEDIA_ITEM_IMAGE)),
    );
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
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

  it('should call navigator api correctly when user clicks on share button on a video', () => {
    mockNavigator.canShare.and.returnValue(true);
    mockNavigator.share.and.resolveTo(undefined);
    mockWebApiService.getMediaItem.and.returnValue(
      of(toSuccess(MEDIA_ITEM_VIDEO)),
    );
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(GPHOTOS_MEDIA_ITEM_VIDEO)),
    );
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem2',
        },
        isOpen: true,
      },
    });
    store.refreshState();
    fixture.autoDetectChanges();

    const shareButton = fixture.nativeElement.querySelector(
      '[data-testid="media-viewer-share-button"]',
    );
    shareButton.click();

    expect(mockNavigator.share).toHaveBeenCalledWith({
      title: 'dog.mp4',
      text: 'Photo from Sharded Photos Drive',
      url: 'http://www.google.com/videos/1=dv',
    });
  });

  it('should not call navigator.share() when user clicks on share button but sharing fails', () => {
    mockNavigator.canShare.and.returnValue(false);
    mockNavigator.share.and.resolveTo(undefined);
    mockWebApiService.getMediaItem.and.returnValue(
      of(toSuccess(MEDIA_ITEM_IMAGE)),
    );
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(GPHOTOS_MEDIA_ITEM_IMAGE)),
    );
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
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
    mockWebApiService.getMediaItem.and.returnValue(
      of(toSuccess(MEDIA_ITEM_IMAGE)),
    );
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(GPHOTOS_MEDIA_ITEM_IMAGE)),
    );
    store.setState({
      [mediaViewerState.FEATURE_KEY]: {
        request: {
          mediaItemId: 'mediaItem1',
        },
        isOpen: true,
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
