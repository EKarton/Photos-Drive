import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { WINDOW } from '../../../../../app.tokens';
import { authState } from '../../../../../auth/store';
import { toPending, toSuccess } from '../../../../../shared/results/results';
import { GetGPhotosMediaItemDetailsResponse } from '../../../../services/types/gphotos-media-item';
import { GPhotosMediaItem } from '../../../../services/types/gphotos-media-item';
import { WebApiService } from '../../../../services/webapi.service';
import { dialogActions, dialogState } from '../../../../store/dialog';
import { ImageComponent } from '../image.component';
import { MediaViewerRequest } from '../../../../media-viewer/media-viewer.request';

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
  let mockWebApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'getGPhotosMediaItem',
    ]);

    await TestBed.configureTestingModule({
      imports: [ImageComponent],
      providers: [
        provideNoopAnimations(),
        provideMockStore({
          initialState: {
            [dialogState.FEATURE_KEY]: dialogState.initialState,
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
    mockWindow = TestBed.inject(WINDOW);
  });

  it('should render skeleton when media item is not loaded yet', () => {
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toPending<GetGPhotosMediaItemDetailsResponse>()),
    );

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

  it('should fetch gphotos media item and render image when it is in viewport', () => {
    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1)),
    );
    const fixture = TestBed.createComponent(ImageComponent);
    fixture.componentRef.setInput('mediaItemId', 'photos1');
    fixture.componentRef.setInput('gPhotosMediaItemId', 'gPhotos1');
    fixture.componentRef.setInput('fileName', 'dog.png');
    fixture.componentRef.setInput('width', 250);
    fixture.componentRef.setInput('height', 300);
    fixture.detectChanges();

    fixture.componentInstance.setIsInViewport(true);
    fixture.detectChanges();

    expect(mockWebApiService.getGPhotosMediaItem).toHaveBeenCalledWith(
      'mockAccessToken',
      { gPhotosMediaItemId: 'gPhotos1' },
    );

    const image = fixture.nativeElement.querySelector(
      '[data-testid="media-item-image"]',
    );
    expect(image.src).toEqual('http://www.google.com/photos/1');
    expect(image.width).toEqual(250);
    expect(image.width).toEqual(250);
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
      mockWebApiService.getGPhotosMediaItem.and.returnValue(
        of(toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1)),
      );
      const fixture = TestBed.createComponent(ImageComponent);
      fixture.componentRef.setInput('mediaItemId', 'photos1');
      fixture.componentRef.setInput('gPhotosMediaItemId', 'gPhotos1');
      fixture.componentRef.setInput('fileName', 'dog.png');
      fixture.componentRef.setInput('width', 250);
      fixture.componentRef.setInput('height', 300);
      fixture.detectChanges();
      fixture.componentInstance.setIsInViewport(true);
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
      mockWebApiService.getGPhotosMediaItem.and.returnValue(
        of(toSuccess(G_MEDIA_ITEM_DETAILS_PHOTO_1)),
      );
      const fixture = TestBed.createComponent(ImageComponent);
      fixture.componentRef.setInput('mediaItemId', 'photos1');
      fixture.componentRef.setInput('gPhotosMediaItemId', 'gPhotos1');
      fixture.componentRef.setInput('fileName', 'dog.png');
      fixture.componentRef.setInput('width', 250);
      fixture.componentRef.setInput('height', 300);
      fixture.detectChanges();
      fixture.componentInstance.setIsInViewport(true);
      fixture.detectChanges();

      fixture.nativeElement
        .querySelector('[data-testid="media-item-image"]')
        .dispatchEvent(event);

      expect(store.dispatch).toHaveBeenCalledWith(
        dialogActions.openDialog({
          request: new MediaViewerRequest('photos1'),
        }),
      );
    });
  });
});
