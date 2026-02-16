import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { authState } from '../../../../../../auth/store';
import {
  toFailure,
  toPending,
  toSuccess,
} from '../../../../../../shared/results/results';
import { GetMediaItemImageResponse } from '../../../../../services/web-api/types/get-media-item-image';
import { WebApiService } from '../../../../../services/web-api/web-api.service';
import { ImageMapMarkerComponent } from '../image-map-marker.component';

const MEDIA_ITEM_ID = 'client1:photos1';

const MEDIA_ITEM_IMAGE_URL = 'http://www.google.com/photos/1';

describe('ImageMapMarkerComponent', () => {
  let store: MockStore;
  let mockWebApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'getMediaItemImage',
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
    mockWebApiService.getMediaItemImage.and.returnValue(
      of(toPending<GetMediaItemImageResponse>()),
    );

    const fixture = TestBed.createComponent(ImageMapMarkerComponent);
    fixture.componentRef.setInput('mediaItemId', MEDIA_ITEM_ID);
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector(
      '[data-testid="image-loading"]',
    );
    expect(spinner).toBeTruthy();
  });

  it('should render error when fetching media item failed', () => {
    mockWebApiService.getMediaItemImage.and.returnValue(
      of(toFailure<GetMediaItemImageResponse>(new Error('Random error'))),
    );

    const fixture = TestBed.createComponent(ImageMapMarkerComponent);
    fixture.componentRef.setInput('mediaItemId', MEDIA_ITEM_ID);
    fixture.detectChanges();
    fixture.componentInstance.setIsInViewport(true);
    fixture.detectChanges();

    const failedMessage = fixture.nativeElement.querySelector(
      '[data-testid="image-failed"]',
    );
    expect(failedMessage).toBeTruthy();
  });

  it('should fetch gphotos media item and render image when it is in viewport', () => {
    mockWebApiService.getMediaItemImage.and.returnValue(
      of(toSuccess({ url: MEDIA_ITEM_IMAGE_URL })),
    );

    const fixture = TestBed.createComponent(ImageMapMarkerComponent);
    fixture.componentRef.setInput('mediaItemId', MEDIA_ITEM_ID);
    fixture.detectChanges();
    fixture.componentInstance.setIsInViewport(true);
    fixture.detectChanges();

    const image = fixture.nativeElement.querySelector(
      '[data-testid="image-loaded"]',
    );
    expect(image).toBeTruthy();
    expect(mockWebApiService.getMediaItemImage).toHaveBeenCalledWith(
      'mockAccessToken',
      MEDIA_ITEM_ID,
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
      mockWebApiService.getMediaItemImage.and.returnValue(
        of(toSuccess({ url: MEDIA_ITEM_IMAGE_URL })),
      );
      const fixture = TestBed.createComponent(ImageMapMarkerComponent);
      fixture.componentRef.setInput('mediaItemId', MEDIA_ITEM_ID);
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
