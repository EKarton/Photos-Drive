import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { authState } from '../../../../../../../auth/store';
import {
  toFailure,
  toPending,
  toSuccess,
} from '../../../../../../../shared/results/results';
import {
  GPhotosMediaItem,
  GPhotosMediaItemDetailsApiResponse,
} from '../../../../../../services/types/gphotos-media-item';
import { MediaItem } from '../../../../../../services/types/media-item';
import { WebApiService } from '../../../../../../services/webapi.service';
import { ImageMapMarkerComponent } from '../image-map-marker.component';

const MEDIA_ITEM: MediaItem = {
  id: 'photos1',
  fileName: 'cat.png',
  hashCode: '',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
  width: 200,
  height: 300,
  dateTaken: new Date('2024-05-27T13:17:46.000Z'),
};

const G_MEDIA_ITEM: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/photos/1',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: '4032',
    height: '3024',
  },
};

describe('ImageMapMarkerComponent', () => {
  let store: MockStore;
  let mockWebApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'getGPhotosMediaItem',
    ]);

    await TestBed.configureTestingModule({
      imports: [ImageMapMarkerComponent],
      providers: [
        provideNoopAnimations(),
        provideMockStore({
          selectors: [
            { selector: authState.selectAuthToken, value: 'mockAccessToken' },
          ],
        }),
        {
          provide: WebApiService,
          useValue: mockWebApiService,
        },
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    spyOn(store, 'dispatch');
  });

  it('should render skeleton when media item is not loaded yet', () => {
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toPending<GPhotosMediaItemDetailsApiResponse>()),
    );

    const fixture = TestBed.createComponent(ImageMapMarkerComponent);
    fixture.componentRef.setInput('mediaItem', MEDIA_ITEM);
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="image-loading"]',
    );
    expect(spinner).toBeTruthy();
  });

  it('should render error when fetching media item failed', () => {
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(
        toFailure<GPhotosMediaItemDetailsApiResponse>(
          new Error('Random error'),
        ),
      ),
    );

    const fixture = TestBed.createComponent(ImageMapMarkerComponent);
    fixture.componentRef.setInput('mediaItem', MEDIA_ITEM);
    fixture.detectChanges();
    fixture.componentInstance.setIsInViewport(true);
    fixture.detectChanges();

    const failedMessage = fixture.nativeElement.querySelector(
      '[data-testid="image-failed"]',
    );
    expect(failedMessage).toBeTruthy();
  });

  it('should fetch gphotos media item and render image when it is in viewport', () => {
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(G_MEDIA_ITEM)),
    );

    const fixture = TestBed.createComponent(ImageMapMarkerComponent);
    fixture.componentRef.setInput('mediaItem', MEDIA_ITEM);
    fixture.detectChanges();
    fixture.componentInstance.setIsInViewport(true);
    fixture.detectChanges();

    const image = fixture.nativeElement.querySelector(
      '[data-testid="image-loaded"]',
    );
    expect(image).toBeTruthy();
    expect(mockWebApiService.getGPhotosMediaItem).toHaveBeenCalledWith(
      'mockAccessToken',
      'gPhotosClient1:gPhotosMediaItem1',
    );
  });

  [
    {
      event: new KeyboardEvent('keydown', {
        key: 'Space',
        code: 'Space',
      }),
    },
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
    it(`should emit event when user emits event ${event} on image`, () => {
      mockWebApiService.getGPhotosMediaItem.and.returnValue(
        of(toSuccess(G_MEDIA_ITEM)),
      );
      const fixture = TestBed.createComponent(ImageMapMarkerComponent);
      fixture.componentRef.setInput('mediaItem', MEDIA_ITEM);
      fixture.detectChanges();
      fixture.componentInstance.setIsInViewport(true);
      fixture.detectChanges();
      let emitted = false;
      fixture.componentInstance.markerClick.subscribe(() => {
        emitted = true;
      });

      fixture.nativeElement.querySelector('div').dispatchEvent(event);

      expect(emitted).toBeTrue();
    });
  });
});
